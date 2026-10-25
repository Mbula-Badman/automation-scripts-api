#!/usr/bin/env python3
"""Check visible CSV files for malformed CSV quoting."""

import csv

from _project_utils import emit_report, project_files, relative_path


def main():
    files, errors = project_files()
    csv_files = [path for path in files if path.suffix.lower() == ".csv"]
    failures = []
    for path in csv_files:
        try:
            with path.open(encoding="utf-8-sig", newline="") as source:
                for _row in csv.reader(source, strict=True):
                    pass
        except (OSError, UnicodeError, csv.Error) as error:
            failures.append({"path": relative_path(path), "error": str(error)})

    report = {
        "checked_files": len(csv_files),
        "invalid_files": failures,
        "scan_errors": errors,
    }
    return emit_report(report, bool(failures or errors))


if __name__ == "__main__":
    raise SystemExit(main())
