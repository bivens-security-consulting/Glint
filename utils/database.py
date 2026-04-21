import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import closing

class GlintDB:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_dir = os.path.join("projects", project_name)
        self.db_path = os.path.join(self.project_dir, f"{project_name}.db")
        
        # Ensure the project directory exists
        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir)
            
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _initialize_db(self):
        """Create tables if they don't exist."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            # Targets table: tracks what needs to be scanned
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    url TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'PENDING',
                    last_updated DATETIME
                )
            """)
            # Results table: tracks findings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    url TEXT PRIMARY KEY,
                    status_code INTEGER,
                    title TEXT,
                    screenshot TEXT,
                    technologies TEXT,
                    headers TEXT,
                    timestamp DATETIME,
                    error TEXT,
                    FOREIGN KEY (url) REFERENCES targets (url)
                )
            """)
            conn.commit()

    def sync_targets(self, urls: List[str]):
        """Upsert targets into the DB. Don't overwrite COMPLETED ones."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            for url in urls:
                cursor.execute("""
                    INSERT OR IGNORE INTO targets (url, status, last_updated)
                    VALUES (?, 'PENDING', ?)
                """, (url, datetime.now().isoformat()))
            conn.commit()

    def get_pending_targets(self) -> List[str]:
        """Fetch all URLs that haven't been successfully scanned yet."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM targets WHERE status != 'COMPLETED'")
            return [row[0] for row in cursor.fetchall()]

    def save_result(self, result: Dict):
        """Save a scan result and update target status."""
        url = result.get('url')
        status = 'COMPLETED' if result.get('screenshot') else 'FAILED'
        
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            # Update target status
            cursor.execute("""
                UPDATE targets SET status = ?, last_updated = ? WHERE url = ?
            """, (status, datetime.now().isoformat(), url))
            
            # Upsert result
            cursor.execute("""
                INSERT OR REPLACE INTO results (
                    url, status_code, title, screenshot, technologies, headers, timestamp, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url,
                result.get('status'),
                result.get('title'),
                result.get('screenshot'),
                json.dumps(result.get('technologies', [])),
                json.dumps(dict(result.get('headers', {}))),
                result.get('timestamp'),
                result.get('error')
            ))
            conn.commit()

    def get_all_results(self) -> List[Dict]:
        """Fetch all results for reporting."""
        with closing(self._get_connection()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM results ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                res = dict(row)
                res['status'] = res.pop('status_code') # rename for report compatibility
                res['technologies'] = json.loads(res['technologies'])
                res['headers'] = json.loads(res['headers'])
                results.append(res)
            return results

    @staticmethod
    def list_projects() -> List[str]:
        """List all project names found in the projects directory."""
        projects_dir = "projects"
        if not os.path.exists(projects_dir):
            return []
        return [
            d for d in os.listdir(projects_dir) 
            if os.path.isdir(os.path.join(projects_dir, d))
        ]

    def get_stats(self) -> Dict:
        """Get statistics for the current project."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM targets")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM targets WHERE status = 'COMPLETED'")
            completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM targets WHERE status = 'FAILED'")
            failed = cursor.fetchone()[0]
            
            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": total - completed - failed
            }

    @staticmethod
    def reset_project(project_name: str):
        """Delete the project database file and folder structure."""
        project_dir = os.path.join("projects", project_name)
        db_path = os.path.join(project_dir, f"{project_name}.db")
        
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            # We don't necessarily delete the whole folder to preserve screenshots, 
            # unless we explicitly want a full wipe. 
            # For 'reset_project', deleting the DB is usually enough to clear findings.
            return True
        except Exception:
            return False
