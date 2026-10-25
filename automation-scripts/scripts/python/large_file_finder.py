#!/usr/bin/env python3
"""List project files larger than five mebibytes."""

from _project_utils import emit_report, project_files, relative_path

LIMIT_BYTES = 5 * 1024 * 1024
MAX_RESULTS = 50


def main():
    files, errors = project_files()
    large_files = []
    for path in files:
        try:
            size = path.stat().st_size
        except OSError as error:
            errors.append(f"{relative_path(path)}: {error}")
            continue
        if size > LIMIT_BYTES:
            large_files.append({"path": relative_path(path), "bytes": size})

    large_files.sort(key=lambda item: (-item["bytes"], item["path"]))
    report = {
        "threshold_bytes": LIMIT_BYTES,
        "files_over_threshold": large_files[:MAX_RESULTS],
        "total_over_threshold": len(large_files),
        "result_limit": MAX_RESULTS,
        "scan_errors": errors,
    }
    return emit_report(report, bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
