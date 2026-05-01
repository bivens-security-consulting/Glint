# Glint | Web Enumeration Control Center

**Glint** is a high-performance web reconnaissance suite built for modern offensive engagements. Built with a **Dashboard-First** architecture, Glint eliminates host-level dependency hell using Docker while providing a real-time "Control Center" for monitoring web discovery.

## Key Features

- **Project Management Hub**: View all your engagements at a glance with a real-time 3-wide project grid and live stats.
- **Real-time Live Activity Feed**: Watch screenshots and status discoveries pop into your dashboard instantly.
- **URL Extraction (Hunting)**: Automatically extract all valid links from landing pages to discover hidden attack surface.
- **API-First Architecture**: Pure JSON output mode for seamless integration into automation pipelines.
- **Zero-Install Deployment (Docker)**: Run Glint with a single command. Playwright, Chromium, and Node.js are fully containerized.
- **Nmap XML Web Ingestor**: Upload Nmap XML files directly to instantly populate your target list.
- **Secure Settings Control**: Manage concurrency, timeouts, and proxychains via a persistent, lockable UI.

---

## Installation & Setup

### Docker (Recommended / Cross-Platform)
The recommended way to run Glint is via Docker, as it bundles all browser dependencies and Node.js requirements.

1. **Start the Control Center**:
   ```bash
   docker-compose up -d --build
   ```
2. **Access the Dashboard**:
   Open [http://localhost:8000](http://localhost:8000)

### Windows Native
Glint can run natively on Windows without a global Node.js/NPM installation.

1. **Install Requirements**:
   ```powershell
   pip install -r requirements.txt
   ```
2. **Setup Browsers**:
   ```powershell
   playwright install chromium
   ```

### Linux Native (Kali/Debian)
Linux requires a few extra steps to handle system-level browser dependencies and the Playwright driver.

1. **Install System Dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y nodejs npm
   # Ensure 'node' command is available
   sudo ln -s /usr/bin/nodejs /usr/bin/node
   ```
2. **Install Requirements & Browsers**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   # Install required Linux shared libraries
   playwright install-deps
   ```

---

## Dashboard Usage
The Dashboard is the primary way to manage projects and view real-time results.

### Launching the Dashboard
```bash
python glint.py dash
```
Access at [http://localhost:8000](http://localhost:8000).

---

## CLI Usage
The CLI is a powerful helper for headless scanning or integrating Glint into other automation pipelines.

### Single Target Mode
```bash
python glint.py scan "https://google.com" --extract-links
```

### Bulk Resume Mode
Glint tracks state per project. If you use a project name, it will only scan **pending** targets.
```bash
python glint.py scan -i targets.txt -p InternalAlpha
```

### API Mode (JSON Output)
Use the `--json` flag to receive a pure JSON payload for piping into tools like `jq`.
```bash
python glint.py scan -i targets.txt --json | jq '.[].extracted_urls[]'
```

### Running CLI via Docker
```bash
# Perform a scan inside the container
docker exec -it glint-app python glint.py scan -i targets.txt --json
```

| Flag | Description |
| :--- | :--- |
| `target` | (Optional) A single URL to scan directly from the command line. |
| `-i, --input` | Path to a line-delimited target file. |
| `-p, --project` | Project name. Defaults to `CLI_Scan`. |
| `--force` | Force a full re-scan of all targets. |
| `--extract-links` | Scrape all `<a>` tags on the page. |
| `--json` | Output pure JSON to `stdout`. |
| `--proxychains` | Optimize network timing for proxychains usage. |

---

## Configuration
Managed via the **Settings** tab in the Dashboard or `python glint.py config`.

| Option | Description |
| :--- | :--- |
| `concurrency` | Number of simultaneous browser instances (default: 5). |
| `timeout` | Page load timeout in milliseconds (default: 30000). |
| `insecure` | Ignore SSL/TLS certificate errors. |
| `output_dir` | Local path for project storage (default: projects). |

---

## Troubleshooting

### "node not found" on Linux
Ensure you have installed `nodejs` and created the symlink:
```bash
sudo ln -s /usr/bin/nodejs /usr/bin/node
```

### Missing shared libraries (Linux)
If browsers fail to launch, run:
```bash
playwright install-deps
```

---

## Security Disclaimer
Glint is intended for use by security professionals for authorized testing only. Users must ensure legal authorization before scanning web services.

## License
MIT License - Created by Bivens Security Consulting.
