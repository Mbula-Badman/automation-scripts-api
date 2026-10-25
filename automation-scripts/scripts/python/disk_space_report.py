#!/usr/bin/env python3
"""Report disk space for the drive containing the current project."""

import json
import shutil
from pathlib import Path

WARNING_PERCENT = 85


def main():
    root = Path.cwd()
    usage = shutil.disk_usage(root)
    used_percent = round(usage.used / usage.total * 100, 1) if usage.total else 0
    status = "warning" if used_percent >= WARNING_PERCENT else "ok"
    report = {
        "volume": root.anchor or str(root),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "used_percent": used_percent,
        "warning_threshold_percent": WARNING_PERCENT,
        "status": status,
    }
    print(json.dumps(report, indent=2))
    return 1 if status == "warning" else 0


if __name__ == "__main__":
    raise SystemExit(main())
