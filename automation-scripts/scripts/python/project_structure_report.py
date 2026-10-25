#!/usr/bin/env python3
"""Summarize visible project folders and file extensions."""

from collections import Counter
from pathlib import Path

from _project_utils import emit_report, project_files, relative_path


def main():
    files, errors = project_files()
    extensions = Counter()
    directories = Counter()
    for path in files:
        extensions[path.suffix.lower() or "[no extension]"] += 1
        relative_parts = Path(relative_path(path)).parent.parts
        for index in range(1, len(relative_parts)):
            directories["/".join(relative_parts[:index])] += 1

    report = {
        "file_count": len(files),
        "directory_file_counts": [
            {"directory": name, "files": count}
            for name, count in sorted(
                directories.items(), key=lambda item: (-item[1], item[0])
            )[:50]
        ],
        "files_by_extension": dict(sorted(extensions.items())),
        "scan_errors": errors,
    }
    return emit_report(report, bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
