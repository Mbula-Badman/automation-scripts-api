-- Automation Scripts dashboard schema (PostgreSQL)
-- Apply with:  psql "$DATABASE_URL" -f db/schema.sql

CREATE TABLE IF NOT EXISTS scripts (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    language    TEXT NOT NULL CHECK (language IN ('bash', 'python')),
    category    TEXT NOT NULL DEFAULT 'general',
    path        TEXT NOT NULL,            -- relative to project root, must be under scripts/
    args        TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS runs (
    id          SERIAL PRIMARY KEY,
    script_id   INTEGER NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    status      TEXT NOT NULL DEFAULT 'running'
                CHECK (status IN ('running', 'ok', 'warning', 'failed', 'timeout')),
    exit_code   INTEGER,
    output      TEXT,
    error       TEXT,
    data        JSONB,                    -- parsed output when the script printed JSON
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_runs_script_started ON runs (script_id, started_at DESC);

INSERT INTO scripts (name, description, language, category, path, args) VALUES
    ('System Health Check', 'Disk, memory, load and uptime report with threshold alerts.',
     'bash', 'monitoring', 'scripts/bash/health_check.sh', ARRAY['-j']),
    ('SSH Log Analyzer', 'Flags IPs with repeated failed SSH logins in an auth log.',
     'python', 'security', 'scripts/python/log_analyzer.py', ARRAY['samples/auth.log', '--json'])
ON CONFLICT (name) DO NOTHING;
