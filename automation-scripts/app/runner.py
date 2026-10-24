"""Runs a registered script and records the result in a local database.

Security: scripts are looked up by id from the database, never from user input,
must live under scripts/, and are run without a shell.
"""
import json
import subprocess
from pathlib import Path

from .db import get_cursor, is_sqlite_database

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
INTERPRETERS = {"bash": "bash", "python": "python3"}
TIMEOUT_SECONDS = 60


def _status_from_exit(code):
    # Our scripts use: 0 = ok, 1 = findings/warnings, anything else = error
    return {0: "ok", 1: "warning"}.get(code, "failed")


def _parse_args(raw_args):
    if raw_args in (None, ""):
        return []
    if isinstance(raw_args, str):
        try:
            return json.loads(raw_args)
        except ValueError:
            return [raw_args]
    return list(raw_args)


def run_script(script_id):
    with get_cursor() as cur:
        if is_sqlite_database():
            cur.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
        else:
            cur.execute("SELECT * FROM scripts WHERE id = %s", (script_id,))
        script = cur.fetchone()
    if script is None:
        raise ValueError("Unknown script")

    path = (ROOT / script["path"]).resolve()
    interpreter = INTERPRETERS.get(script["language"])
    if interpreter is None or SCRIPTS_DIR not in path.parents or not path.is_file():
        raise ValueError("Script path or language not allowed")

    args = _parse_args(script["args"])
    with get_cursor(commit=True) as cur:
        if is_sqlite_database():
            cur.execute("INSERT INTO runs (script_id, status) VALUES (?, 'running')", (script_id,))
            run_id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        else:
            cur.execute("INSERT INTO runs (script_id) VALUES (%s) RETURNING id", (script_id,))
            run_id = cur.fetchone()["id"]

    cmd = [interpreter, str(path), *args]
    status, exit_code, out, err = "failed", None, "", ""
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              timeout=TIMEOUT_SECONDS)
        exit_code, out, err = proc.returncode, proc.stdout, proc.stderr
        status = _status_from_exit(exit_code)
    except subprocess.TimeoutExpired:
        status, err = "timeout", f"Timed out after {TIMEOUT_SECONDS}s"
    except OSError as e:
        err = str(e)

    try:
        data = json.loads(out) if out.strip() else None
    except ValueError:
        data = None

    with get_cursor(commit=True) as cur:
        if is_sqlite_database():
            cur.execute(
                """UPDATE runs
                   SET status = ?, exit_code = ?, output = ?, error = ?, data = ?, finished_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (status, exit_code, out, err, json.dumps(data) if data is not None else None, run_id),
            )
        else:
            cur.execute(
                """UPDATE runs SET status=%s, exit_code=%s, output=%s, error=%s,
                          data=%s, finished_at=now() WHERE id=%s""",
                (status, exit_code, out, err, json.dumps(data) if data is not None else None, run_id),
            )
    return run_id
