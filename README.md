# Glint | Web Enumeration Control Center

**Glint** is a high-performance web reconnaissance suite built for modern offensive engagements. Built with a **Dashboard-First** architecture, Glint eliminates host-level dependency hell using Docker while providing a real-time "Control Center" for monitoring web discovery.

![Glint Dashboard Mockup](https://raw.githubusercontent.com/bivens-security-consulting/Glint/main/assets/preview.png)

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

## CLI Usage (Helper)

The CLI is a lean helper for launching quick scans or updating the project config without touching the UI.

```bash
# Start a scan using the shared config
python glint.py scan -pj InternalAlpha -i targets.txt

# Launch the dashboard from the terminal
python glint.py dash

# View current configuration
python glint.py config
```

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
