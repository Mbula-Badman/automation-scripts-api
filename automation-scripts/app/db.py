import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = Path(__file__).resolve().parent.parent


def is_sqlite_database():
    return os.environ.get("DATABASE_URL", f"sqlite:///{ROOT / 'automation_scripts.db'}").startswith("sqlite")


def ensure_schema():
    database_url = os.environ.get("DATABASE_URL", f"sqlite:///{ROOT / 'automation_scripts.db'}")
    if database_url.startswith("sqlite"):
        db_path = str((ROOT / "automation_scripts.db").resolve()) if database_url.startswith("sqlite:///") else database_url.replace("sqlite:///", "", 1)
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    language TEXT NOT NULL CHECK (language IN ('bash', 'python')),
                    category TEXT NOT NULL DEFAULT 'general',
                    path TEXT NOT NULL,
                    args TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id INTEGER NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
                    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'ok', 'warning', 'failed', 'timeout')),
                    exit_code INTEGER,
                    output TEXT,
                    error TEXT,
                    data TEXT,
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_runs_script_started
                ON runs (script_id, started_at DESC)
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO scripts (name, description, language, category, path, args)
                VALUES
                    ('System Health Check', 'Disk, memory, load and uptime report with threshold alerts.', 'bash', 'monitoring', 'scripts/bash/health_check.sh', '[\"-j\"]'),
                    ('SSH Log Analyzer', 'Flags IPs with repeated failed SSH logins in an auth log.', 'python', 'security', 'scripts/python/log_analyzer.py', '[\"samples/auth.log\", \"--json\"]'),
                    ('Workspace Inventory', 'Counts project files, groups them by extension, and lists the largest files without changing anything.', 'python', 'productivity', 'scripts/python/workspace_inventory.py', '[]'),
                    ('Disk Space Report', 'Shows used and free space on the drive containing this project, with a warning above 85%.', 'python', 'monitoring', 'scripts/python/disk_space_report.py', '[]'),
                    ('Python Environment Snapshot', 'Reports the Python version, operating system, architecture, and available CPU count.', 'python', 'diagnostics', 'scripts/python/environment_snapshot.py', '[]'),
                    ('Python Syntax Check', 'Checks project Python files for syntax errors without executing them.', 'python', 'quality', 'scripts/python/python_syntax_check.py', '[]'),
                    ('JSON File Check', 'Validates project JSON files and reports malformed files.', 'python', 'quality', 'scripts/python/json_file_check.py', '[]'),
                    ('CSV File Check', 'Checks project CSV files for malformed CSV syntax.', 'python', 'quality', 'scripts/python/csv_file_check.py', '[]'),
                    ('TODO Finder', 'Finds TODO, FIXME, and XXX notes in project source files.', 'python', 'productivity', 'scripts/python/todo_finder.py', '[]'),
                    ('Large File Finder', 'Lists project files larger than 5 MB to help spot storage-heavy files.', 'python', 'productivity', 'scripts/python/large_file_finder.py', '[]'),
                    ('Duplicate File Finder', 'Finds identical project files by size and SHA-256 without deleting anything.', 'python', 'productivity', 'scripts/python/duplicate_file_finder.py', '[]'),
                    ('Recent Files Report', 'Lists project files modified in the last seven days.', 'python', 'productivity', 'scripts/python/recent_files_report.py', '[]'),
                    ('Requirements Audit', 'Summarizes dependencies listed in requirements.txt without installing or contacting package indexes.', 'python', 'quality', 'scripts/python/requirements_audit.py', '[]'),
                    ('Git Status Snapshot', 'Shows the current local Git branch and working-tree changes, if this is a Git repository.', 'python', 'diagnostics', 'scripts/python/git_status_snapshot.py', '[]'),
                    ('Project Structure Report', 'Summarizes project folders and file counts by extension.', 'python', 'productivity', 'scripts/python/project_structure_report.py', '[]')
                """
            )
            conn.commit()
        return

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scripts (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    language TEXT NOT NULL CHECK (language IN ('bash', 'python')),
                    category TEXT NOT NULL DEFAULT 'general',
                    path TEXT NOT NULL,
                    args TEXT[] NOT NULL DEFAULT '{}'
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id SERIAL PRIMARY KEY,
                    script_id INTEGER NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
                    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'ok', 'warning', 'failed', 'timeout')),
                    exit_code INTEGER,
                    output TEXT,
                    error TEXT,
                    data JSONB,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    finished_at TIMESTAMPTZ
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_runs_script_started ON runs (script_id, started_at DESC)"
            )
            cur.execute(
                """
                INSERT INTO scripts (name, description, language, category, path, args) VALUES
                    ('System Health Check', 'Disk, memory, load and uptime report with threshold alerts.', 'bash', 'monitoring', 'scripts/bash/health_check.sh', ARRAY['-j']),
                    ('SSH Log Analyzer', 'Flags IPs with repeated failed SSH logins in an auth log.', 'python', 'security', 'scripts/python/log_analyzer.py', ARRAY['samples/auth.log', '--json']),
                    ('Workspace Inventory', 'Counts project files, groups them by extension, and lists the largest files without changing anything.', 'python', 'productivity', 'scripts/python/workspace_inventory.py', ARRAY[]::TEXT[]),
                    ('Disk Space Report', 'Shows used and free space on the drive containing this project, with a warning above 85%.', 'python', 'monitoring', 'scripts/python/disk_space_report.py', ARRAY[]::TEXT[]),
                    ('Python Environment Snapshot', 'Reports the Python version, operating system, architecture, and available CPU count.', 'python', 'diagnostics', 'scripts/python/environment_snapshot.py', ARRAY[]::TEXT[]),
                    ('Python Syntax Check', 'Checks project Python files for syntax errors without executing them.', 'python', 'quality', 'scripts/python/python_syntax_check.py', ARRAY[]::TEXT[]),
                    ('JSON File Check', 'Validates project JSON files and reports malformed files.', 'python', 'quality', 'scripts/python/json_file_check.py', ARRAY[]::TEXT[]),
                    ('CSV File Check', 'Checks project CSV files for malformed CSV syntax.', 'python', 'quality', 'scripts/python/csv_file_check.py', ARRAY[]::TEXT[]),
                    ('TODO Finder', 'Finds TODO, FIXME, and XXX notes in project source files.', 'python', 'productivity', 'scripts/python/todo_finder.py', ARRAY[]::TEXT[]),
                    ('Large File Finder', 'Lists project files larger than 5 MB to help spot storage-heavy files.', 'python', 'productivity', 'scripts/python/large_file_finder.py', ARRAY[]::TEXT[]),
                    ('Duplicate File Finder', 'Finds identical project files by size and SHA-256 without deleting anything.', 'python', 'productivity', 'scripts/python/duplicate_file_finder.py', ARRAY[]::TEXT[]),
                    ('Recent Files Report', 'Lists project files modified in the last seven days.', 'python', 'productivity', 'scripts/python/recent_files_report.py', ARRAY[]::TEXT[]),
                    ('Requirements Audit', 'Summarizes dependencies listed in requirements.txt without installing or contacting package indexes.', 'python', 'quality', 'scripts/python/requirements_audit.py', ARRAY[]::TEXT[]),
                    ('Git Status Snapshot', 'Shows the current local Git branch and working-tree changes, if this is a Git repository.', 'python', 'diagnostics', 'scripts/python/git_status_snapshot.py', ARRAY[]::TEXT[]),
                    ('Project Structure Report', 'Summarizes project folders and file counts by extension.', 'python', 'productivity', 'scripts/python/project_structure_report.py', ARRAY[]::TEXT[])
                ON CONFLICT (name) DO NOTHING
                """
            )
            conn.commit()


@contextmanager
def get_cursor(commit=False):
    """Yield a dict-like cursor, automatically using SQLite when no PostgreSQL URL is configured."""
    database_url = os.environ.get("DATABASE_URL", f"sqlite:///{ROOT / 'automation_scripts.db'}")
    if database_url.startswith("sqlite"):
        db_path = str((ROOT / "automation_scripts.db").resolve()) if database_url.startswith("sqlite:///") else database_url.replace("sqlite:///", "", 1)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            yield cur
            if commit:
                conn.commit()
        finally:
            conn.close()
        return

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()
