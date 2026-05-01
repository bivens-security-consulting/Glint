# Glint | Web Enumeration Control Center

**Glint** is a high-performance web reconnaissance suite built for modern offensive engagements. Built with a **Dashboard-First** architecture, Glint eliminates host-level dependency hell using Docker while providing a real-time "Control Center" for monitoring web discovery.

## Key Features

- **Real-time Live Activity Feed**: Watch screenshots and status discoveries pop into your dashboard instantly as Glint captures them.
- **Dynamic Gallery Injection**: The frontend gallery automatically adds new screenshot cards without requiring a page refresh.
- **Zero-Install Deployment (Docker)**: Run Glint with a single command. Playwright, Chromium, and all dependencies are fully containerized.
- **Nmap XML Web Ingestor**: Upload Nmap XML files directly in the browser to instantly populate your target list.
- **Secure Settings Hub**: Manage concurrency, timeouts, and proxychains via a persistent, lockable configuration UI.
- **Technology Fingerprinting**: Automatically identify CMS, servers, and frameworks (React, Next.js, Nginx, etc.).
- **Smart Logic**: Multi-project support with SQLite persistence, cumulative project reporting, and intelligent URL normalization.

---

## Quick Start (Dockerized)

The recommended way to run Glint is via **Docker Compose** for full persistence and zero configuration.

1. **Start the Control Center**:
   ```bash
   docker-compose up -d --build
   ```
2. **Access the Dashboard**:
   Open [http://localhost:8000](http://localhost:8000)

---

## CLI & API Usage
The CLI is a powerful helper for headless scanning or integrating Glint into other automation pipelines (API mode).

### Standard Scanning
```bash
# Basic scan with default reporting
python glint.py scan -i targets.txt

# Scan using proxychains and extract all links from landing pages
python glint.py scan -i targets.txt --proxychains --extract-links
```

### API Mode (JSON Output)
Use the `--json` flag to suppress human-readable output and receive a pure JSON payload. This is ideal for piping into other tools like `jq` or external APIs.

```bash
# Scan and pipe results into a JSON file
python glint.py scan -i targets.txt --extract-links --json > results.json

# Extract only valid URLs discovered from the scan
python glint.py scan -i targets.txt --extract-links --json | jq '.[].extracted_urls[]'
```

| Flag | Description |
| :--- | :--- |
| `-i, --input` | Path to the line-delimited target file. |
| `--extract-links` | Scrape and resolve all `<a>` tags on the page. |
| `--json` | Output pure JSON to `stdout` (logs/errors go to `stderr`). |
| `--proxychains` | Optimize network timing for proxychains. |

---

## Remote File Access
Glint stores all assets in the `projects/` directory. When running as an API, you can retrieve screenshots by referencing the `screenshot` filename returned in the JSON payload:
- **Local Path**: `projects/screenshots/<filename>`
- **Web App (if running)**: `http://localhost:8000/media/screenshots/<filename>`

---

## Project Structure

Glint keeps your data organized by engagement:
- `projects/`: Root directory for all scan data.
  - `{ProjectName}.db`: Persistence layer.
  - `{ProjectName}_report.html`: Cumulative searchable report.
  - `screenshots/`: High-fidelity visual evidence.

---

## Configuration

Configuration is stored in `.glint_config.yaml` and can be managed via the **Settings** tab in the Dashboard.

| Option | Description |
| :--- | :--- |
| `concurrency` | Number of simultaneous Playwright instances. |
| `timeout` | Page load timeout in seconds. |
| `proxychains` | Enable TOR/Proxychains routing. |

---

## Security Disclaimer

Glint is intended for use by security professionals for authorized testing only. Users must ensure legal authorization before scanning web services.

## License
MIT License - Created by Bivens Security Consulting.
