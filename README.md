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

## Quick Start (Dockerized)

The recommended way to run Glint is via **Docker Compose**.

1. **Start the Control Center**:
   ```bash
   docker-compose up -d --build
   ```
2. **Access the Dashboard**:
   Open [http://localhost:8000](http://localhost:8000)

---

## CLI & API Usage
The CLI is a powerful helper for headless scanning or integrating Glint into other automation pipelines.

### Single Target Mode
Scan a target directly without a file:
```bash
python glint.py scan "https://google.com" --extract-links
```

### Bulk Resume Mode
Glint tracks state per project. If you use a project name, it will only scan **pending** targets.
```bash
python glint.py scan -i targets.txt -p InternalAlpha
```

### API Mode (JSON Output)
Use the `--json` flag to receive a pure JSON payload. This suppresses headers and logs to `stderr`, keeping `stdout` clean for parsing tools like `jq`.

```bash
# Extract all discovered URLs from a scan using jq
python glint.py scan -i targets.txt --json | jq '.[].extracted_urls[]'
```

| Flag | Description |
| :--- | :--- |
| `target` | (Optional) A single URL to scan directly from the command line. |
| `-i, --input` | Path to a line-delimited target file. |
| `-p, --project` | Project name. Defaults to `CLI_Scan` (which always re-scans all targets). |
| `--force` | Force a full re-scan of all targets even in a named project. |
| `--extract-links` | Scrape all `<a>` tags on the page and include in report/JSON. |
| `--json` | Output pure JSON to `stdout`. |
| `--proxychains` | Optimize network timing for proxychains usage. |

### Running CLI via Docker (Zero-Install)
If you have the Docker container running, you can execute CLI commands inside the container to avoid installing dependencies (Python, Playwright, etc.) on your host machine. This is useful if you are having issues with Playwright on your host machine.

```bash
# Perform a scan inside the container
docker exec -it glint-app python glint.py scan -i targets.txt --json

# View config inside the container
docker exec -it glint-app python glint.py config
```

---

## Linux Troubleshooting
If you encounter missing binary errors (like `/usr/bin/node`) when running natively on Linux:
```bash
sudo apt-get update && sudo apt-get install -y nodejs npm
sudo ln -s /usr/bin/nodejs /usr/bin/node
```
*(Note: The Docker image is unaffected as it uses a pre-configured Playwright environment.)*

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

## Security Disclaimer
Glint is intended for use by security professionals for authorized testing only. Users must ensure legal authorization before scanning web services.

## License
MIT License - Created by Bivens Security Consulting.
