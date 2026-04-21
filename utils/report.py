import os
from datetime import datetime
from jinja2 import Environment, BaseLoader

# --- HTML Template ---
REPORT_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Glint Report - {{ stats.timestamp }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #080808;
            --card-bg: #111111;
            --accent-color: #ffffff;
            --text-primary: #f2f2f2;
            --text-secondary: #888888;
            --border-color: #222222;
            --border-active: #ffffff;
            --shadow-soft: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            --radius: 12px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', system-ui, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            padding: 4rem 2rem;
            line-height: 1.6;
        }

        header {
            margin-bottom: 4rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 2rem;
        }

        .title-group h1 {
            font-size: 3rem;
            font-weight: 700;
            color: var(--accent-color);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .stats {
            display: flex;
            gap: 3rem;
        }

        .stat-item { text-align: left; }
        .stat-value { font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .stat-label { font-size: 0.7rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.15em; }

        /* Filter Controls */
        .controls-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
            gap: 2rem;
        }

        .filter-bar {
            display: flex;
            gap: 0.5rem;
            background: #111;
            padding: 0.4rem;
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }

        .filter-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.4rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            transition: all 0.2s;
        }

        .filter-btn.active {
            background: var(--accent-color);
            color: #000;
        }

        .filter-btn:hover:not(.active) {
            background: #222;
            color: #fff;
        }

        .search-wrapper { flex-grow: 1; }
        #searchInput {
            width: 100%;
            background-color: transparent;
            border: none;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.5rem 0;
            font-size: 1.25rem;
            outline: none;
            transition: border-color 0.3s;
        }
        #searchInput:focus { border-bottom-color: var(--border-active); }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 3rem;
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: block;
        }

        .card:hover {
            border-color: var(--border-active);
            box-shadow: var(--shadow-soft);
            transform: translateY(-4px);
        }

        .screenshot-container {
            width: 100%;
            height: 280px;
            overflow: hidden;
            background-color: #000;
            position: relative;
            border-bottom: 1px solid var(--border-color);
        }

        .screenshot-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: all 0.5s ease;
        }

        .card:hover .screenshot-container img { transform: scale(1.02); }

        .card-content { padding: 2rem; }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .url {
            font-weight: 600; font-size: 1rem; color: var(--text-primary);
            text-decoration: none; word-break: break-all;
            font-family: 'JetBrains Mono', monospace;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
        }

        .status-2xx { background: #fff; color: #000; }
        .status-4xx { background: #222; color: #fff; border: 1px solid #444; }
        .status-5xx { background: #444; color: #fff; }
        .status-error { background: #000; color: #666; border: 1px solid #222; }

        .tech-badges { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 1.5rem; }
        .tech-badge { border: 1px solid #222; color: #888; padding: 0.1rem 0.4rem; font-size: 0.65rem; border-radius: 4px; text-transform: uppercase; }

        .title { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; font-weight: 500; }
        .metadata { font-size: 0.75rem; color: #555; font-family: 'JetBrains Mono', monospace; }
        .meta-item b { color: #aaa; }

        footer { margin-top: 8rem; padding: 4rem 0; border-top: 1px solid var(--border-color); color: #333; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.2em; }
    </style>
</head>
<body>
    <header>
        <div class="title-group">
            <h1 style="text-transform: capitalize;">{{ stats.project_name }} Report</h1>
            <p style="color: var(--text-secondary)">{{ stats.timestamp }}</p>
        </div>
        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 1rem;">
            <div style="font-size: 0.7rem; letter-spacing: 0.3em; color: #444; font-weight: 800; margin-bottom: -0.5rem;">GLINT</div>
            <div class="stats">
            <div class="stat-item">
                <span class="stat-value">{{ stats.total }}</span>
                <span class="stat-label">Total</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{{ stats.successful }}</span>
                <span class="stat-label">Successful</span>
            </div>
            <div class="stat-item">
                <span class="stat-value" style="color: #666">{{ stats.failed }}</span>
                <span class="stat-label">Failed</span>
            </div>
        </div>
    </header>

    <div class="controls-row">
        <div class="filter-bar">
            <button class="filter-btn active" data-filter="all">All</button>
            <button class="filter-btn" data-filter="2xx">2xx</button>
            <button class="filter-btn" data-filter="3xx">3xx</button>
            <button class="filter-btn" data-filter="4xx">4xx</button>
            <button class="filter-btn" data-filter="5xx">5xx</button>
        </div>
        <div class="search-wrapper">
            <input type="text" id="searchInput" placeholder="Search targets, titles, or tech...">
        </div>
    </div>

    <div class="grid" id="resultsGrid">
        {% for result in results %}
        {% set status_group = 'error' %}
        {% if result.status is number %}
            {% if result.status >= 200 and result.status < 300 %}{% set status_group = '2xx' %}
            {% elif result.status >= 300 and result.status < 400 %}{% set status_group = '3xx' %}
            {% elif result.status >= 400 and result.status < 500 %}{% set status_group = '4xx' %}
            {% elif result.status >= 500 %}{% set status_group = '5xx' %}
            {% endif %}
        {% endif %}
        <div class="card" data-status="{{ status_group }}">
            <div class="screenshot-container">
                {% if result.screenshot %}
                <a href="../screenshots/{{ result.screenshot }}" target="_blank">
                    <img src="../screenshots/{{ result.screenshot }}" alt="Screenshot of {{ result.url }}">
                </a>
                {% else %}
                <div class="no-screenshot">UNREACHABLE</div>
                {% endif %}
            </div>
            <div class="card-content">
                <div class="card-header">
                    <a href="{{ result.url }}" class="url" target="_blank">{{ result.url }}</a>
                    <span class="status-badge status-{{ status_group }}">
                        {% if status_group == '2xx' %}
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                        {% elif status_group == '4xx' %}
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                        {% elif status_group == '5xx' %}
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                        {% endif %}
                        {{ result.status if result.status is number else 'FAIL' }}
                    </span>
                </div>
                <div class="title" title="{{ result.title }}">{{ result.title or 'NO PAGE TITLE' }}</div>
                <div class="metadata">
                    <div class="meta-item">SERVER: <b>{{ (result.headers.get('server') or result.headers.get('Server') or 'N/A') }}</b></div>
                </div>
                <div class="tech-badges">
                    {% for tech in result.technologies %}
                    <span class="tech-badge">{{ tech }}</span>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <footer>Generated by Glint &bull; Web Enumeration Tool</footer>

    <script>
        const searchInput = document.getElementById('searchInput');
        const resultsGrid = document.getElementById('resultsGrid');
        const cards = Array.from(resultsGrid.getElementsByClassName('card'));
        const filterBtns = document.querySelectorAll('.filter-btn');
        let currentFilter = 'all';

        function applyFilters() {
            const term = searchInput.value.toLowerCase();
            cards.forEach(card => {
                const status = card.getAttribute('data-status');
                const text = card.innerText.toLowerCase();
                const matchesSearch = text.includes(term);
                const matchesFilter = (currentFilter === 'all' || status === currentFilter);
                
                card.style.display = (matchesSearch && matchesFilter) ? 'block' : 'none';
            });
        }

        searchInput.addEventListener('input', applyFilters);

        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.getAttribute('data-filter');
                applyFilters();
            });
        });
    </script>
</body>
</html>
"""

# --- REPORT LOGIC ---
class GlintReport:
    def __init__(self, output_dir: str, session_time: str = ""):
        self.output_dir = output_dir
        self.session_time = session_time or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.env = Environment(loader=BaseLoader())

    def generate(self, results: list, project_name: str = "Default"):
        os.makedirs(self.output_dir, exist_ok=True)
        template = self.env.from_string(REPORT_TEMPLATE)
        sorted_results = sorted(results, key=lambda x: str(x.get('status', '0')) if isinstance(x.get('status'), int) else '0', reverse=True)
        total = len(results)
        successful = len([r for r in results if r.get('screenshot')])
        failed = total - successful
        html_content = template.render(
            results=sorted_results,
            stats={
                "project_name": project_name,
                "total": total,
                "successful": successful,
                "failed": failed,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        report_path = os.path.join(self.output_dir, f"report_{self.session_time}.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return report_path
