#!/usr/bin/env python3
"""Validate visible JSON files in the project."""

import json

from _project_utils import emit_report, project_files, relative_path


def main():
    files, errors = project_files()
    json_files = [path for path in files if path.suffix.lower() == ".json"]
    failures = []
    for path in json_files:
        try:
            with path.open(encoding="utf-8-sig") as source:
                json.load(source)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            failures.append({"path": relative_path(path), "error": str(error)})

    report = {
        "checked_files": len(json_files),
        "invalid_files": failures,
        "scan_errors": errors,
    }
    return emit_report(report, bool(failures or errors))


if __name__ == "__main__":
    raise SystemExit(main())
