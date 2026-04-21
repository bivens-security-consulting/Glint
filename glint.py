import asyncio
import os
import sys
import click
import webbrowser
from datetime import datetime
from rich.console import Console
from utils.dashboard import GlintDashboard
from utils.config import GlintConfig
from utils.engine import GlintEngine
from utils.report import GlintReport
from utils.database import GlintDB

console = Console()

@click.group()
def cli():
    """Glint: A powerful web enumeration tool.
    
    Automates the discovery of web services, captures high-fidelity screenshots, 
    detects underlying technology stacks, and manages targets via a persistent 
    project-based SQLite backend.
    """
    console.print(r"""[bold cyan]
  ________.__  .__        __   
 /  _____/|  | |__| _____/  |_ 
/   \  ___|  | |  |/    \   __\
\    \_\  \  |_|  |   |  \  |  
 \______  /____/__|___|  /__|  
        \/             \/      
    [/bold cyan]""")
    console.print(f"[bold white]Glint v0.6.0[/bold white] | [dim]Web Enumeration Tool[/dim]\n")

@cli.command()
@click.argument('key', required=False)
@click.argument('value', required=False)
def config(key, value):
    """View or update persistent configuration."""
    if not key:
        cfg = GlintConfig.load()
        console.print("[bold cyan]Current Configuration:[/bold cyan]")
        for k, v in cfg.items():
            console.print(f"  [bold]{k}[/bold]: {v}")
        return

    if not value:
        cfg = GlintConfig.load()
        if key in cfg:
            console.print(f"{key}: {cfg[key]}")
        else:
            console.print(f"[red][!][/red] Key '{key}' not found in config.")
        return

    # Try to cast value to int or bool if applicable
    if value.lower() == 'true': value = True
    elif value.lower() == 'false': value = False
    else:
        try:
            value = int(value)
        except ValueError:
            pass

    if GlintConfig.set(key, value):
        console.print(f"[green][+][/green] Updated [bold]{key}[/bold] to [bold]{value}[/bold]")
    else:
        console.print(f"[red][!][/red] Failed to update configuration.")

@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True), help='Path to targets list.')
@click.option('--proxychains', is_flag=True, help='Optimize for use with proxychains.')
def scan(input, proxychains):
    """Run a quick scan from the command line using global configuration."""
    if not input:
        console.print("[red][!][/red] No input file provided.")
        return

    config = GlintConfig.load()
    project = "CLI_Scan"
    db = GlintDB(project)
    session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(db.project_dir, f"scan_{session_time}")
    
    # Load targets
    with open(input, 'r') as f:
        targets = [line.strip() for line in f if line.strip()]
    
    # Basic expansion if protocol is missing
    urls = []
    for t in targets:
        if t.startswith(('http://', 'https://')): urls.append(t)
        else:
            urls.append(f"http://{t}")
            urls.append(f"https://{t}")
            
    db.sync_targets(urls)
    pending = db.get_pending_targets()
    
    # Proxy handling
    effective_proxy = config.get('proxy')
    if proxychains or config.get('proxychains'):
        console.print("[*] Proxychains mode enabled.")
        effective_proxy = None

    engine = GlintEngine(
        output_dir=output_dir,
        proxy=effective_proxy,
        concurrency=config.get('concurrency', 5),
        timeout=config.get('timeout', 30000),
        session_time=session_time,
        insecure=config.get('insecure', True),
        detect_tech=config.get('tech', True),
        db=db
    )
    
    console.print(f"[*] Starting CLI scan of {len(pending)} targets...")
    results = asyncio.run(engine.run(pending))
    
    report_gen = GlintReport(output_dir, session_time=session_time)
    report_path = report_gen.generate(results, project_name=project)
    
    console.print(f"\n[green][+][/green] Scan complete! Report: [bold]{report_path}[/bold]")

@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind the dashboard to.')
@click.option('--port', default=8000, help='Port to bind the dashboard to.')
def dash(host, port):
    """Launch the web management dashboard."""
    console.print(f"[*] Launching Control Center: [bold]http://{host}:{port}[/bold]")
    
    # Only auto-open if we are NOT in a docker container
    if not os.environ.get('GLINT_DOCKER'):
        try:
            webbrowser.open(f"http://{host}:{port}")
        except Exception:
            pass
            
    dashboard = GlintDashboard(host=host, port=port)
    dashboard.run()

if __name__ == "__main__":
    # If no arguments provided, default to 'dash'
    if len(sys.argv) == 1:
        sys.argv.append('dash')
    cli()
