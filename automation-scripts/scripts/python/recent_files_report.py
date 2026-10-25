#!/usr/bin/env python3
"""List project files modified within the previous seven days."""

import time

from _project_utils import emit_report, project_files, relative_path

DAYS = 7
MAX_RESULTS = 100


def main():
    files, errors = project_files()
    cutoff = time.time() - DAYS * 24 * 60 * 60
    recent = []
    for path in files:
        try:
            modified = path.stat().st_mtime
        except OSError as error:
            errors.append(f"{relative_path(path)}: {error}")
            continue
        if modified >= cutoff:
            recent.append(
                {
                    "path": relative_path(path),
                    "modified_unix": int(modified),
                    "modified_local": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(modified)
                    ),
                }
            )

    recent.sort(key=lambda item: (-item["modified_unix"], item["path"]))
    report = {
        "lookback_days": DAYS,
        "recent_files": recent[:MAX_RESULTS],
        "total_recent_files": len(recent),
        "result_limit": MAX_RESULTS,
        "scan_errors": errors,
    }
    return emit_report(report, bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
