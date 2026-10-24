import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, url_for

load_dotenv()

from .db import ensure_schema, get_cursor  # noqa: E402
from .runner import run_script  # noqa: E402

app = Flask(__name__)
ensure_schema()


def _as_datetime(value):
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    return value


def _normalize_record(record):
    if record is None:
        return None
    normalized = dict(record)
    for key in ("started_at", "finished_at", "last_started"):
        if key in normalized:
            normalized[key] = _as_datetime(normalized[key])
    return normalized


@app.route("/")
def index():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                s.*,
                (
                    SELECT r.id
                    FROM runs r
                    WHERE r.script_id = s.id
                    ORDER BY r.started_at DESC
                    LIMIT 1
                ) AS last_run_id,
                (
                    SELECT r.status
                    FROM runs r
                    WHERE r.script_id = s.id
                    ORDER BY r.started_at DESC
                    LIMIT 1
                ) AS last_status,
                (
                    SELECT r.started_at
                    FROM runs r
                    WHERE r.script_id = s.id
                    ORDER BY r.started_at DESC
                    LIMIT 1
                ) AS last_started
            FROM scripts s
            ORDER BY s.category, s.name
            """
        )
        scripts = [_normalize_record(row) for row in cur.fetchall()]
    return render_template("index.html", scripts=scripts)


@app.post("/run/<int:script_id>")
def run(script_id):
    try:
        run_id = run_script(script_id)
    except ValueError:
        abort(404)
    return redirect(url_for("run_detail", run_id=run_id))


@app.route("/runs")
def runs():
    with get_cursor() as cur:
        cur.execute(
            """SELECT r.*, s.name FROM runs r JOIN scripts s ON s.id = r.script_id
               ORDER BY r.started_at DESC LIMIT 100"""
        )
        rows = [_normalize_record(row) for row in cur.fetchall()]
    return render_template("runs.html", runs=rows)


@app.route("/runs/<int:run_id>")
def run_detail(run_id):
    with get_cursor() as cur:
        database_url = os.environ.get("DATABASE_URL", "sqlite:///automation_scripts.db")
        if "sqlite" in database_url:
            cur.execute(
                """SELECT r.*, s.name FROM runs r JOIN scripts s ON s.id = r.script_id
                   WHERE r.id = ?""", (run_id,))
        else:
            cur.execute(
                """SELECT r.*, s.name FROM runs r JOIN scripts s ON s.id = r.script_id
                   WHERE r.id = %s""", (run_id,))
        row = _normalize_record(cur.fetchone())
    if row is None:
        abort(404)
    return render_template("run_detail.html", run=row)
