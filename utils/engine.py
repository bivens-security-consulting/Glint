import asyncio
import os
import json
from datetime import datetime
from typing import List, Optional, Dict
from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from slugify import slugify
from utils.fingerprint import GlintFingerprinter

import sys
console = Console()

class GlintEngine:
    def __init__(self, output_dir: str, proxy: Optional[str] = None, concurrency: int = 5, timeout: int = 30000, session_time: str = "", insecure: bool = True, detect_tech: bool = True, db: Optional[object] = None, extract_links: bool = False, quiet: bool = False):
        self.output_dir = output_dir
        self.screenshots_dir = os.path.join(os.path.dirname(output_dir), "screenshots")
        self.proxy = proxy
        self.concurrency = concurrency
        self.timeout = timeout
        self.session_time = session_time or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.insecure = insecure
        self.detect_tech = detect_tech
        self.extract_links = extract_links
        self.quiet = quiet
        self.db = db
        self.console = Console(file=sys.stderr) if quiet else console
        self.fingerprinter = GlintFingerprinter() if detect_tech else None
        self.results = []
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)

    async def screenshot_url(self, browser_context, url: str) -> Dict:
        page = await browser_context.new_page()
        result = {
            "url": url,
            "status": "failed",
            "title": "",
            "screenshot": "",
            "timestamp": datetime.now().isoformat(),
            "headers": {},
            "technologies": [],
            "extracted_urls": [],
            "error": None
        }
        try:
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            # Use domcontentloaded first, then wait for load. More stable for redirects.
            response = await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            await page.wait_for_load_state("load", timeout=self.timeout)
            
            # Let the page "settle" for 2 seconds to avoid capturing loading spinners or mid-redirect states
            await page.wait_for_timeout(2000)
            
            if response:
                result["status"] = response.status
                result["headers"] = response.headers
                
                # Attempt to get title, but don't fail if context is destroyed during redirect
                try:
                    result["title"] = await page.title()
                except Exception:
                    result["title"] = "Title Unavailable (Navigation Race)"

                # Technology Fingerprinting
                if self.detect_tech:
                    try:
                        content = await page.content()
                        result["technologies"] = self.fingerprinter.detect(response.headers, content)
                    except Exception as e:
                        self.console.print(f"[yellow][!][/yellow] Fingerprinting failed for {url}: {str(e)}")

                # URL Extraction
                if self.extract_links:
                    try:
                        links = await page.locator("a").evaluate_all("elements => elements.map(el => el.href).filter(h => h)")
                        result["extracted_urls"] = list(set(links))
                    except Exception as e:
                        self.console.print(f"[yellow][!][/yellow] Link extraction failed for {url}: {str(e)}")

                # Add timestamp to screenshot filename
                filename = f"{slugify(url)}_{self.session_time}.png"
                screenshot_path = os.path.join(self.screenshots_dir, filename)
                
                # Try-catch specifically for the screenshot as well
                try:
                    await page.screenshot(path=screenshot_path, full_page=False)
                    result["screenshot"] = filename
                except Exception as e:
                    self.console.print(f"[yellow][!][/yellow] Screenshot failed for {url}: {str(e)}")
                
                self.console.print(f"[green][+][/green] Scanned: {url} ({response.status})")
            else:
                result["error"] = "No response"
                self.console.print(f"[red][![/red] No response from: {url}")
        except Exception as e:
            result["error"] = str(e)
            self.console.print(f"[red][!][/red] Error scanning {url}: {str(e)}")
        finally:
            await page.close()
        return result

    async def run(self, urls: List[str]):
        async with async_playwright() as p:
            # Playwright expects the protocol (http:// or socks5://)
            proxy_config = None
            if self.proxy:
                server_url = self.proxy
                if not server_url.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
                    server_url = f"socks5://{server_url}"
                proxy_config = {"server": server_url}
            
            # Passing proxy to launch() is more robust on Windows for Chromium
            launch_args = ["--ignore-certificate-errors"] if self.insecure else []
            browser = await p.chromium.launch(
                headless=True, 
                proxy=proxy_config,
                args=launch_args
            )
            context = await browser.new_context(ignore_https_errors=self.insecure)
            semaphore = asyncio.Semaphore(self.concurrency)
            async def semi_bounded_screenshot(url):
                async with semaphore:
                    res = await self.screenshot_url(context, url)
                    self.results.append(res)
                    if self.db:
                        self.db.save_result(res)
            tasks = [semi_bounded_screenshot(url) for url in urls]
            if not self.quiet:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), console=self.console) as progress:
                    task = progress.add_task("[cyan]Enumerating URLs...", total=len(urls))
                    for coro in asyncio.as_completed(tasks):
                        await coro
                        progress.update(task, advance=1)
            else:
                for coro in asyncio.as_completed(tasks):
                    await coro
            await browser.close()
            # Save results in a unique json file
            results_path = os.path.join(self.output_dir, f"results_{self.session_time}.json")
            with open(results_path, "w") as f:
                json.dump(self.results, f, indent=4)
            return self.results
