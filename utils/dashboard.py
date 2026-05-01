import os
import threading
import json
import shutil
from datetime import datetime
import traceback
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from utils.database import GlintDB
from utils.engine import GlintEngine
from utils.report import GlintReport
from utils.config import GlintConfig
from utils.parsers import GlintParser
import asyncio

# --- Dashboard Templates ---
DASHBOARD_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Glint | Web Enumeration Tool</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #050505;
            --sidebar: #0a0a0a;
            --card: #111;
            --accent: #fff;
            --text: #eee;
            --dim: #777;
            --border: #222;
            --radius: 12px;
            --shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        * { margin:0; padding:0; box-sizing: border-box; }
        body { 
            background: var(--bg); color: var(--text); 
            font-family: 'Inter', sans-serif; display: flex; height: 100vh; overflow: hidden;
        }

        /* Sidebar */
        aside {
            width: 280px; background: var(--sidebar); border-right: 1px solid var(--border);
            display: flex; flex-direction: column; padding: 2rem 1.5rem;
        }
        .logo { font-size: 1.5rem; font-weight: 800; margin-bottom: 3rem; color: var(--accent); letter-spacing: -1px; }
        .nav-section { margin-bottom: 2rem; }
        .nav-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--dim); margin-bottom: 1rem; }
        .project-list { list-style: none; overflow-y: auto; flex-grow: 1; }
        .project-item {
            padding: 0.8rem 1rem; border-radius: 8px; cursor: pointer; margin-bottom: 0.4rem;
            transition: 0.2s; color: var(--dim); font-size: 0.9rem; text-decoration: none; display: flex; align-items: center; gap: 0.8rem;
        }
        .project-item:hover { background: #151515; color: #fff; }
        .project-item.active { background: #fff; color: #000; font-weight: 600; }
        .project-item .delete-proj { margin-left: auto; opacity: 0; transition: 0.2s; padding: 4px; }
        .project-item:hover .delete-proj { opacity: 0.4; }
        .project-item .delete-proj:hover { opacity: 1; color: #ff4444; }

        /* Main Content */
        main { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; }
        .top-bar { padding: 2rem 3rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .view-controls { padding: 1.5rem 3rem; border-bottom: 1px solid var(--border); background: #080808; display: flex; gap: 2rem; align-items: center; }
        
        .search-box { flex-grow: 1; position: relative; }
        .search-box input {
            width: 100%; background: transparent; border: none; color: #fff; font-size: 1.1rem; outline: none;
            padding: 0.5rem 0; border-bottom: 1px solid transparent; transition: 0.3s;
        }
        .search-box input:focus { border-bottom-color: var(--accent); }

        .filter-group { display: flex; gap: 0.5rem; align-items: center; }
        .filter-btn {
            background: #111; color: var(--dim); border: 1px solid var(--border);
            padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer; transition: 0.2s;
        }
        .filter-btn.active { background: var(--accent); color: #000; border-color: var(--accent); }

        .content-scroll { flex-grow: 1; overflow-y: auto; padding: 2rem 3rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 2.5rem; }

        /* Cards */
        .card {
            background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
            overflow: hidden; transition: 0.3s cubic-bezier(0.4,0,0.2,1); cursor: pointer; position: relative;
        }
        .card:hover { transform: translateY(-4px); border-color: var(--accent); box-shadow: var(--shadow); }
        .img-wrap { width: 100%; height: 200px; background: #000; overflow: hidden; border-bottom: 1px solid var(--border); position: relative; }
        .img-wrap img { width: 100%; height: 100%; object-fit: cover; transition: 0.5s; }
        .card:hover .img-wrap img { transform: scale(1.05); }
        .status-badge {
            position: absolute; top: 12px; right: 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 800;
            padding: 2px 8px; border-radius: 4px; background: #000; border: 1px solid var(--border);
        }
        .badge-2xx { color: #00ff88; border-color: #00ff8844; }
        .badge-4xx { color: #ffbb00; }
        .badge-5xx { color: #ff4444; }

        .card-info { padding: 1.5rem; }
        .card-url { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--accent); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 0.4rem; font-weight: 500; }
        .card-title { font-size: 0.75rem; color: var(--dim); font-weight: 400; margin-bottom: 1rem; }
        .tech-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; }
        .tag { font-size: 0.6rem; color: var(--dim); border: 1px solid #222; padding: 1px 6px; border-radius: 3px; text-transform: uppercase; font-weight: 700; }

        /* Detail Modal */
        #detailModal {
            display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 200;
            backdrop-filter: blur(10px); padding: 4rem; overflow-y: auto;
        }
        .modal-inner { max-width: 1200px; margin: 0 auto; display: flex; gap: 4rem; }
        .modal-left { flex: 1; }
        .modal-right { width: 400px; }
        .modal-img { width: 100%; border-radius: var(--radius); border: 1px solid var(--border); box-shadow: var(--shadow); margin-bottom: 2rem; }
        .modal-header { margin-bottom: 2rem; }
        .modal-url { font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; color: var(--accent); margin-bottom: 0.5rem; display: block; overflow-wrap: break-word; }
        .modal-title { font-size: 1.1rem; color: var(--dim); }
        
        .info-block { margin-bottom: 2.5rem; }
        .info-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--dim); margin-bottom: 1rem; display: block; }
        .header-list { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; background: #0a0a0a; padding: 1.2rem; border-radius: 8px; border: 1px solid var(--border); line-height: 1.6; }
        .header-item { margin-bottom: 0.2rem; }
        .header-key { color: var(--dim); }
        .header-val { color: var(--text); }
        
        .close-modal { position: fixed; top: 2rem; right: 3rem; font-size: 2rem; color: var(--dim); cursor: pointer; transition: 0.2s; z-index: 210; }
        .close-modal:hover { color: #fff; transform: rotate(90deg); }

        /* Buttons */
        .btn {
            background: var(--accent); color: #000; border: none; padding: 0.8rem 1.6rem; border-radius: 8px; font-weight: 700; cursor: pointer;
            transition: 0.2s; display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem;
        }
        .btn:hover { background: #ccc; }
        .btn-dim { background: #111; color: var(--dim); border: 1px solid var(--border); }
        .btn-dim:hover { background: #1a1a1a; color: #fff; border-color: var(--accent); }

        /* Scan Modal */
        #scanModal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 300; align-items: center; justify-content: center; }
        .scan-box { background: #0f0f0f; width: 500px; padding: 3rem; border-radius: 20px; border: 1px solid var(--border); box-shadow: var(--shadow); }
        textarea { width: 100%; height: 200px; background: #000; border: 1px solid var(--border); color: #fff; padding: 1rem; border-radius: 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin: 1.5rem 0; outline: none; }
        textarea:focus, input:focus { border-color: var(--accent); }
        .form-group { margin-bottom: 1.5rem; }
        .form-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
        .form-row > div { flex: 1; }
        input[type="checkbox"] { filter: invert(1); cursor: pointer; }

        /* Progress Bar */
        .progress-container { width: 100%; height: 4px; background: #111; position: relative; margin-top: 1rem; border-radius: 2px; overflow: hidden; }
        #progressBar { width: 0%; height: 100%; background: #00ff88; transition: 0.5s; }

        /* Activity Log */
        .activity-section { margin-top: 2rem; border-top: 1px solid var(--border); padding-top: 1.5rem; }
        .activity-log { height: 150px; overflow-y: auto; background: #080808; border: 1px solid var(--border); border-radius: 8px; padding: 1rem; list-style: none; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; }
        .log-item { margin-bottom: 0.4rem; padding-bottom: 0.4rem; border-bottom: 1px dashed #222; display: flex; gap: 1rem; }
        .log-time { color: var(--dim); }
        .log-url { color: var(--accent); }
        .log-status { font-weight: 700; }
        .status-up { color: #00ff88; }
        .status-down { color: #ff4444; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #222; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #333; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .fade-in { animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
    </style>
</head>
<body>
    <aside>
        <div class="logo">GLINT</div>
        <div class="nav-section">
            <div class="nav-label">General</div>
            <a href="/" class="project-item {% if not active_project %}active{% endif %}">Dashboard</a>
            <div class="project-item" onclick="openSettings()">Settings</div>
        </div>
        <div class="nav-section" style="flex-grow:1;">
            <div class="nav-label">Projects</div>
            <div class="project-list" id="projectList">
                {% for p in projects %}
                <div class="project-item {% if p == active_project %}active{% endif %}" onclick="window.location.href='/?project={{p}}'">
                    <span>{{ p }}</span>
                    <span class="delete-proj" onclick="event.stopPropagation(); deleteProject('{{ p }}')">✕</span>
                </div>
                {% endfor %}
            </div>
        </div>

        {% if active_project %}
        <div class="activity-section">
            <div class="nav-label">Live Activity</div>
            <ul class="activity-log" id="activityLog">
                <li style="color:var(--dim); font-style:italic;">Listening for events...</li>
            </ul>
        </div>
        {% endif %}
    </aside>

    <main>
        <div class="top-bar">
            <div>
                <h1>{{ active_project if active_project else 'Manage Projects' }}</h1>
                {% if stats %}
                <div style="font-size: 0.75rem; color: var(--dim); margin-top: 0.5rem; display: flex; gap: 1.5rem;">
                    <span>TOTAL: <b id="statTotal">{{ stats.total }}</b></span>
                    <span>COMPLETED: <b id="statCompleted" style="color: #00ff88;">{{ stats.completed }}</b></span>
                    <span>FAILED: <b id="statFailed" style="color: #ff4444;">{{ stats.failed }}</b></span>
                    <span>PENDING: <b id="statPending">{{ stats.pending }}</b></span>
                </div>
                <div class="progress-container"><div id="progressBar" style="width: {{ (stats.completed + stats.failed) / stats.total * 100 if stats.total > 0 else 0 }}%;"></div></div>
                {% endif %}
            </div>
            <div style="display:flex; gap:1rem;">
                <button class="btn" onclick="openScanModal()">+ New Scan</button>
            </div>
        </div>

        {% if active_project %}
        <div class="view-controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search targets, titles, or headers..." oninput="filterResults()">
            </div>
            <div class="filter-group">
                <button class="filter-btn active" data-filter="all" onclick="setFilter('all')">All</button>
                <button class="filter-btn" data-filter="2xx" onclick="setFilter('2xx')">2xx</button>
                <button class="filter-btn" data-filter="4xx" onclick="setFilter('4xx')">4xx</button>
                <button class="filter-btn" data-filter="5xx" onclick="setFilter('5xx')">5xx</button>
            </div>
        </div>

        <div class="content-scroll">
            <div class="grid" id="resultsGrid">
                {% for res in results %}
                <div class="card" data-url="{{ res.url | lower }}" data-title="{{ (res.title or '') | lower }}" data-status="{{ res.get('status', '0') }}" data-tech="{{ res.technologies | join(' ') | lower }}" onclick="openDetail({{ loop.index0 }})">
                    <div class="img-wrap">
                        {% if res.screenshot_path %}
                        <img src="/media/{{ res.screenshot_path }}" loading="lazy">
                        {% else %}
                        <div style="height:100%; display:flex; align-items:center; justify-content:center; color:#333; font-weight:800;">ERROR</div>
                        <div class="status-badge badge-{{ ((res.get('status', 0)|int(default=0)) // 100) }}xx">{{ res.get('status') or '???' }}</div>
                    </div>
                    <div class="card-info">
                        <div class="card-url">{{ res.url }}</div>
                        <div class="card-title">{{ res.title or 'NO PAGE TITLE' }}</div>
                        <div class="tech-tags">
                            {% for tech in res.technologies %}
                            <span class="tag">{{ tech }}</span>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% else %}
        <div class="content-scroll" style="display:flex; align-items:center; justify-content:center; color:var(--dim);">
            <div style="text-align:center;">
                <h2 style="color:#333; font-size:3rem; margin-bottom:1rem;">Select a project to begin</h2>
                <p>Or click New Scan to start enumerating fresh targets.</p>
            </div>
        </div>
        {% endif %}
    </main>

    <!-- Detail Modal -->
    <div id="detailModal">
        <div class="close-modal" onclick="closeDetail()">✕</div>
        <div class="modal-inner">
            <div class="modal-left">
                <div class="modal-header">
                    <a id="detUrl" href="#" target="_blank" class="modal-url"></a>
                    <div id="detTitle" class="modal-title"></div>
                </div>
                <img id="detImg" src="" class="modal-img">
            </div>
            <div class="modal-right">
                <div class="info-block">
                    <span class="info-label">Technology Stack</span>
                    <div id="detTech" class="tech-tags"></div>
                </div>
                <div class="info-block">
                    <span class="info-label">Response Headers</span>
                    <div id="detHeaders" class="header-list"></div>
                </div>
                <div class="info-block">
                    <span class="info-label">Discovery Meta</span>
                    <div id="detMeta" class="header-list" style="font-size:0.7rem; color:var(--dim);"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scan Modal -->
    <div id="scanModal">
        <div class="scan-box">
            <h2 style="font-size:1.8rem;">Start Enumeration</h2>
            <p style="color:var(--dim); font-size:0.85rem; margin-top:0.5rem;">Create a new project or add to current.</p>
            <div style="margin-top:1.5rem;">
                <label class="info-label">Project Name</label>
                <input type="text" id="scanProject" style="background:#000; border:1px solid var(--border); color:#fff; padding:0.8rem; width:100%; border-radius:12px; outline:none;" value="{{ active_project or 'Glint' }}">
            </div>
            <textarea id="scanTargets" placeholder="http://example.com&#10;https://example.com&#10;127.0.0.1"></textarea>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
                <span style="font-size:0.75rem; color:var(--dim);">Fast Import:</span>
                <button class="btn btn-dim" onclick="triggerNmapUpload()" style="padding: 4px 10px; font-size: 0.7rem;">📁 Import Nmap XML</button>
                <input type="file" id="nmapFile" style="display:none;" accept=".xml" onchange="handleNmapFile(this)">
            </div>
            <div style="display:flex; gap:1rem;">
                <button class="btn" id="startScanBtn" onclick="startScan()" style="flex:1;">Launch Scan</button>
                <button class="btn btn-dim" onclick="closeScanModal()">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Settings Modal -->
    <div id="settingsModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:400; align-items:center; justify-content:center;">
        <div class="scan-box" style="width: 600px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <h2 style="font-size:1.8rem;">Global Settings</h2>
                    <p style="color:var(--dim); font-size:0.85rem; margin-top:0.5rem;">Persistent configuration for all scans.</p>
                </div>
                <button class="btn btn-dim" id="lockBtn" onclick="toggleSettingsLock()" style="padding: 0.5rem 1rem;">🔓 Unlock to Edit</button>
            </div>
            
            <div style="margin-top:2rem;" id="settingsFields">
                <div class="form-row">
                    <div>
                        <label class="info-label">Concurrency</label>
                        <input type="number" id="cfgConcurrency" style="background:#000; border:1px solid var(--border); color:#fff; padding:0.8rem; width:100%; border-radius:12px; outline:none;">
                    </div>
                    <div>
                        <label class="info-label">Timeout (ms)</label>
                        <input type="number" id="cfgTimeout" style="background:#000; border:1px solid var(--border); color:#fff; padding:0.8rem; width:100%; border-radius:12px; outline:none;">
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="info-label">Default Ports</label>
                    <input type="text" id="cfgPorts" style="background:#000; border:1px solid var(--border); color:#fff; padding:0.8rem; width:100%; border-radius:12px; outline:none;">
                </div>

                <div class="form-group">
                    <label class="info-label">SOCKS/HTTP Proxy</label>
                    <input type="text" id="cfgProxy" placeholder="e.g. http://127.0.0.1:8080" style="background:#000; border:1px solid var(--border); color:#fff; padding:0.8rem; width:100%; border-radius:12px; outline:none;">
                </div>

                <div class="form-group">
                    <label class="info-label">Projects Directory</label>
                    <input type="text" id="cfgOutputDir" style="background:#000; border:1px solid var(--border); color:#fff; padding:0.8rem; width:100%; border-radius:12px; outline:none;">
                </div>

                <div class="form-row" style="background:#111; padding:1.2rem; border-radius:12px; border:1px solid #222; flex-wrap: wrap; gap: 1.5rem;">
                    <div style="display:flex; align-items:center; gap:1rem;">
                        <input type="checkbox" id="cfgTech">
                        <label style="font-size:0.8rem; font-weight:600;">Enable Tech Detection</label>
                    </div>
                    <div style="display:flex; align-items:center; gap:1rem;">
                        <input type="checkbox" id="cfgProxychains">
                        <label style="font-size:0.8rem; font-weight:600;">Proxychains Mode</label>
                    </div>
                    <div style="display:flex; align-items:center; gap:1rem;">
                        <input type="checkbox" id="cfgInsecure">
                        <label style="font-size:0.8rem; font-weight:600;">Insecure SSL</label>
                    </div>
                </div>
            </div>

            <div style="display:flex; gap:1rem; margin-top:2rem;">
                <button class="btn" onclick="saveSettings()" style="flex:1;">Save Configuration</button>
                <button class="btn btn-dim" onclick="closeSettings()">Cancel</button>
            </div>
        </div>
    </div>

    <script>
        console.log("[*] Glint Dashboard Script Initializing...");
        const results = {{ results | tojson }};
        const activeProject = "{{ active_project or '' }}";
        let currentFilter = 'all';
        let settingsLocked = true;
        const displayedUrls = new Set(results.map(r => r.url));
        
        window.onload = () => { console.log("[*] Dashboard UI Fully Loaded."); };

        // Polling logic for Live Activity
        if (activeProject) {
            setInterval(async () => {
                try {
                    const resp = await fetch('/api/scan/progress/' + activeProject);
                    if (!resp.ok) return;
                    const data = await resp.json();
                    
                    // Update stats
                    document.getElementById('statTotal').innerText = data.stats.total;
                    document.getElementById('statCompleted').innerText = data.stats.completed;
                    document.getElementById('statFailed').innerText = data.stats.failed;
                    document.getElementById('statPending').innerText = data.stats.pending;
                    
                    const progress = data.stats.total > 0 ? ((data.stats.completed + data.stats.failed) / data.stats.total * 100) : 0;
                    document.getElementById('progressBar').style.width = progress + '%';

                    // Update activity log
                    const log = document.getElementById('activityLog');
                    if (data.recent && data.recent.length > 0) {
                        log.innerHTML = '';
                        data.recent.forEach(item => {
                            const li = document.createElement('li');
                            li.className = 'log-item';
                            const isUp = item.status >= 200 && item.status < 400;
                            li.innerHTML = '<span class="log-url">' + item.url.replace('https://', '').replace('http://', '') + '</span>' +
                                           '<span class="log-status ' + (isUp ? 'status-up' : 'status-down') + '">' + (item.status || 'FAIL') + '</span>';
                            log.appendChild(li);

                            // Live Gallery Update
                            if (!displayedUrls.has(item.url)) {
                                displayedUrls.add(item.url);
                                results.unshift(item); // Add to local results at start
                                injectCard(item);
                            }
                        });
                    }
                } catch (e) { console.error("Poll Error:", e); }
            }, 3000);
        }

        function injectCard(res) {
            const grid = document.getElementById('resultsGrid');
            if (!grid) return;
            const card = document.createElement('div');
            card.className = 'card fade-in';
            card.setAttribute('data-url', res.url.toLowerCase());
            card.setAttribute('data-title', (res.title || '').toLowerCase());
            card.setAttribute('data-status', res.status || '0');
            card.setAttribute('data-tech', (res.technologies || []).join(' ').toLowerCase());
            card.onclick = () => openDetail(results.indexOf(res));

            const imgHtml = res.screenshot_path ? 
                '<img src="/media/' + res.screenshot_path + '" loading="lazy">' :
                '<div style="height:100%; display:flex; align-items:center; justify-content:center; color:#333; font-weight:800;">ERROR</div>';

            const techHtml = (res.technologies || []).map(t => '<span class="tag">' + t + '</span>').join('');

            card.innerHTML = 
                '<div class="img-wrap">' +
                    imgHtml +
                    '<div class="status-badge badge-' + (Math.floor((parseInt(res.status) || 0) / 100)) + 'xx">' + (res.status || '???') + '</div>' +
                '</div>' +
                '<div class="card-info">' +
                    '<div class="card-url">' + res.url + '</div>' +
                    '<div class="card-title">' + (res.title || 'NO PAGE TITLE') + '</div>' +
                    '<div class="tech-tags">' + techHtml + '</div>' +
                '</div>';
            
            grid.insertBefore(card, grid.firstChild);
            filterResults(); // Apply current filters to new card
        }

        function filterResults() {
            const query = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.card');
            cards.forEach(card => {
                const url = card.dataset.url;
                const title = card.dataset.title;
                const tech = card.dataset.tech;
                const status = card.dataset.status;
                const statusGroup = status ? status.charAt(0) + 'xx' : 'error';

                const matchesSearch = url.includes(query) || title.includes(query) || tech.includes(query);
                const matchesFilter = currentFilter === 'all' || statusGroup === currentFilter;

                card.style.display = matchesSearch && matchesFilter ? 'block' : 'none';
            });
        }

        function setFilter(filter) {
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            document.querySelector('[data-filter="' + filter + '"]').classList.add('active');
            filterResults();
        }

        function openDetail(index) {
            const res = results[index];
            document.getElementById('detUrl').innerText = res.url;
            document.getElementById('detUrl').href = res.url;
            document.getElementById('detTitle').innerText = res.title || 'NO PAGE TITLE';
            document.getElementById('detImg').src = res.screenshot_path ? '/media/' + res.screenshot_path : '';
            
            const techWrap = document.getElementById('detTech');
            techWrap.innerHTML = '';
            res.technologies.forEach(t => {
                const s = document.createElement('span'); s.className = 'tag'; s.innerText = t;
                techWrap.appendChild(s);
            });

            const headWrap = document.getElementById('detHeaders');
            headWrap.innerHTML = '';
            for (const [k, v] of Object.entries(res.headers)) {
                const item = document.createElement('div');
                item.className = 'header-item';
                item.innerHTML = '<span class="header-key">' + k + ':</span> <span class="header-val">' + v + '</span>';
                headWrap.appendChild(item);
            }

            document.getElementById('detMeta').innerHTML = 'TIMESTAMP: ' + res.timestamp + '<br>STATUS: ' + res.status + '<br>ERROR: ' + (res.error || 'NONE');

            document.getElementById('detailModal').style.display = 'block';
        }

        function closeDetail() { document.getElementById('detailModal').style.display = 'none'; }

        function openScanModal() { document.getElementById('scanModal').style.display = 'flex'; }
        function closeScanModal() { document.getElementById('scanModal').style.display = 'none'; }

        async function startScan() {
            const project = document.getElementById('scanProject').value.trim();
            const targets = document.getElementById('scanTargets').value.split('\n').filter(t => t.trim() !== '');
            if (!project || targets.length === 0) return alert('Project and targets required');

            const resp = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project, targets })
            });

            if (resp.ok) {
                alert('Scan task dispatched. Refresh project to see new results.');
                window.location.href = '/?project=' + project;
            } else {
                alert('Error starting scan');
            }
        }

        async function deleteProject(name) {
            if (!confirm('Permanently delete project "' + name + '" AND all its files?')) return;
            const resp = await fetch('/api/project/' + name, { method: 'DELETE' });
            if (resp.ok) window.location.href = '/';
            else alert('Error deleting project');
        }

        async function openSettings() {
            try {
                console.log("[*] Opening Settings...");
                const resp = await fetch('/api/config');
                if (!resp.ok) throw new Error("Failed to fetch config");
                const cfg = await resp.json();
                
                document.getElementById('cfgConcurrency').value = cfg.concurrency;
                document.getElementById('cfgTimeout').value = cfg.timeout;
                document.getElementById('cfgPorts').value = cfg.ports;
                document.getElementById('cfgProxy').value = cfg.proxy || '';
                document.getElementById('cfgTech').checked = cfg.tech;
                document.getElementById('cfgProxychains').checked = cfg.proxychains;
                document.getElementById('cfgInsecure').checked = cfg.insecure;
                document.getElementById('cfgOutputDir').value = cfg.output_dir;
                
                // Force lock on open
                settingsLocked = false;
                toggleSettingsLock();
                
                document.getElementById('settingsModal').style.display = 'flex';
            } catch (err) {
                console.error("Settings Error:", err);
                alert("Could not load settings. Check dashboard logs.");
            }
        }

        function closeSettings() { document.getElementById('settingsModal').style.display = 'none'; }

        async function saveSettings() {
            if (settingsLocked) return;
            const cfg = {
                concurrency: parseInt(document.getElementById('cfgConcurrency').value),
                timeout: parseInt(document.getElementById('cfgTimeout').value),
                ports: document.getElementById('cfgPorts').value,
                proxy: document.getElementById('cfgProxy').value || null,
                tech: document.getElementById('cfgTech').checked,
                proxychains: document.getElementById('cfgProxychains').checked,
                insecure: document.getElementById('cfgInsecure').checked,
                output_dir: document.getElementById('cfgOutputDir').value
            };

            const resp = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cfg)
            });

            if (resp.ok) {
                alert('Settings saved successfully');
                toggleSettingsLock(); // Re-lock
                closeSettings();
            } else {
                alert('Error saving settings');
            }
        }

        function toggleSettingsLock() {
            settingsLocked = !settingsLocked;
            const btn = document.getElementById('lockBtn');
            const fields = document.getElementById('settingsFields').querySelectorAll('input');
            
            if (settingsLocked) {
                btn.innerHTML = '🔓 Unlock to Edit';
                btn.classList.add('btn-dim');
                fields.forEach(f => f.disabled = true);
            } else {
                btn.innerHTML = '🔒 Lock Settings';
                btn.classList.remove('btn-dim');
                fields.forEach(f => f.disabled = false);
            }
        }

        function triggerNmapUpload() { document.getElementById('nmapFile').click(); }
        async function handleNmapFile(input) {
            if (!input.files || !input.files[0]) return;
            const file = input.files[0];
            const formData = new FormData();
            formData.append('file', file);

            const resp = await fetch('/api/import/nmap', {
                method: 'POST',
                body: formData
            });

            if (resp.ok) {
                const data = await resp.json();
                const textarea = document.getElementById('scanTargets');
                const existing = textarea.value.trim();
                textarea.value = (existing ? existing + '\n' : '') + data.urls.join('\n');
                alert('Imported ' + data.urls.length + ' targets from Nmap.');
            } else {
                alert('Error parsing Nmap XML');
            }
            input.value = ''; // Reset input
        }
    </script>
</body>
</html>
"""

class GlintDashboard:
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._active_scans = set() 
        
        # Calculate absolute paths for robustness
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.script_dir)
        self.projects_dir = os.path.join(self.project_root, "projects")
        
        self.app.add_url_rule('/', 'index', self.handle_index)
        self.app.add_url_rule('/api/scan', 'api_scan', self.handle_api_scan, methods=['POST'])
        self.app.add_url_rule('/api/scan/progress/<project>', 'api_progress', self.handle_api_progress)
        self.app.add_url_rule('/api/project/<name>', 'delete_project', self.handle_delete_project, methods=['DELETE'])
        self.app.add_url_rule('/api/config', 'get_config', self.handle_get_config)
        self.app.add_url_rule('/api/config', 'set_config', self.handle_set_config, methods=['POST'])
        self.app.add_url_rule('/api/import/nmap', 'import_nmap', self.handle_api_import_nmap, methods=['POST'])
        self.app.add_url_rule('/media/<path:filename>', 'custom_static', self.handle_static)

        # Global Error Handler for Architecture Stability
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            """Return JSON errors and print traceback to console, ignoring 404s."""
            if "404 Not Found" in str(e):
                return jsonify({"error": "Not Found"}), 404
            
            print(f"[!] DASHBOARD ERROR: {str(e)}")
            traceback.print_exc()
            response = {"error": str(e)}
            return jsonify(response), 500

    def handle_index(self):
        active_project = request.args.get('project')
        projects = GlintDB.list_projects()
        
        results = []
        stats = None
        if active_project:
            db = GlintDB(active_project)
            stats = db.get_stats()
            results = self._get_results_with_paths(db, active_project)
                
        return render_template_string(
            DASHBOARD_TEMPLATE,
            projects=projects,
            active_project=active_project,
            results=results,
            stats=stats
        )

    def _get_results_with_paths(self, db, project):
        """Helper to get results and resolve their screenshot paths."""
        raw_results = db.get_all_results()
        results = []
        for res in raw_results:
            if res.get('screenshot'):
                screenshot_name = res['screenshot']
                rel_path = self._find_screenshot_path(project, screenshot_name)
                res['screenshot_path'] = rel_path
            results.append(res)
        return results

    def handle_static(self, filename):
        """Diagnostic static file server with absolute path resolution."""
        # Ensure filename doesn't have a leading slash which can cause issues on some OS/Flask versions
        clean_filename = filename.lstrip('/')
        print(f"[*] Screenshot Request: {clean_filename}")
        return send_from_directory(self.projects_dir, clean_filename)

    def handle_delete_project(self, name):
        """Permanently delete a project and its folder with sanitization."""
        if name in self._active_scans:
            return jsonify({'error': 'Cannot delete project with an active scan running'}), 400
            
        # Sanitize name to prevent path traversal
        safe_name = "".join([c for c in name if c.isalnum() or c in ('_', '-')]).strip()
        if not safe_name:
            return jsonify({'error': 'Invalid project name'}), 400
            
        project_dir = os.path.join(self.projects_dir, safe_name)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            return jsonify({'status': 'deleted'})
        return jsonify({'error': 'Project not found'}), 404

    def _find_screenshot_path(self, project, filename):
        """Find the relative path to a screenshot starting from the projects/ root."""
        project_dir = os.path.join(self.projects_dir, project)
        if not os.path.exists(project_dir):
            print(f"[!] Project directory not found: {project_dir}")
            return None
        for root, _, files in os.walk(project_dir):
            if filename in files:
                full_path = os.path.join(root, filename)
                # Return path relative to the projects_dir NOT the project_dir
                # because our static server is rooted at projects_dir
                rel = os.path.relpath(full_path, self.projects_dir).replace('\\', '/')
                return rel
        print(f"[!] Screenshot not found on disk: {filename} in {project_dir}")
        return None

    def handle_api_import_nmap(self):
        """Parse uploaded Nmap XML and return discovered URLs."""
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        try:
            content = file.read().decode('utf-8')
            urls = GlintParser.parse_nmap_string(content)
            return jsonify({'urls': urls})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def handle_get_config(self):
        """Return current global configuration."""
        return jsonify(GlintConfig.load())

    def handle_set_config(self):
        """Update global configuration."""
        data = request.json
        success = True
        for k, v in data.items():
            if not GlintConfig.set(k, v):
                success = False
        return jsonify({'status': 'success' if success else 'partial_failure'})

    def handle_api_progress(self, project):
        """Fetch project stats and most recent results for the live feed."""
        db = GlintDB(project)
        stats = db.get_stats()
        results = self._get_results_with_paths(db, project) # Resolved paths
        
        return jsonify({
            'stats': stats,
            'recent': results[:8], # Last 8 items
            'is_active': project in self._active_scans
        })

    def handle_api_scan(self):
        data = request.json
        project = data.get('project')
        targets = data.get('targets', [])
        
        if not project or not targets:
            return jsonify({'error': 'Missing project or targets'}), 400
            
        self._active_scans.add(project)
        thread = threading.Thread(target=self._run_scan_thread, args=(project, targets))
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started'})

    def _run_scan_thread(self, project, targets):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._async_scan_task(project, targets))
        loop.close()

    async def _async_scan_task(self, project, targets):
        db = GlintDB(project)
        config = GlintConfig.load()
        
        session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(db.project_dir, f"scan_{session_time}")
        os.makedirs(output_dir, exist_ok=True)
        
        db.sync_targets(targets)
        pending = db.get_pending_targets()
        
        if not pending: return

        # Handle proxychains bypass
        effective_proxy = config.get('proxy')
        if config.get('proxychains'):
            print("[*] Proxychains mode detected via config. Bypassing internal proxy.")
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
        
        await engine.run(pending)
        self._active_scans.discard(project)
        report_gen = GlintReport(output_dir, session_time=session_time)
        report_gen.generate(db.get_all_results(), project_name=project)

    def run(self):
        print(f"[*] Glint Web App (Flask) starting on http://{self.host}:{self.port}")
        print(f"[*] Media Directory: {self.projects_dir}")
        self.app.run(host=self.host, port=self.port, debug=False)
