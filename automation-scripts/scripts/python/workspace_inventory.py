#!/usr/bin/env python3
"""Summarize files in the current project without modifying them."""

import json
import os
import sys
from collections import Counter
from pathlib import Path

EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    "venv",
}


def inventory(root: Path) -> dict:
    extensions = Counter()
    largest_files = []
    total_bytes = 0
    file_count = 0
    skipped_entries = 0

    def record_walk_error(_error):
        nonlocal skipped_entries
        skipped_entries += 1

    for directory, child_directories, filenames in os.walk(
        root, topdown=True, onerror=record_walk_error, followlinks=False
    ):
        child_directories[:] = sorted(
            name
            for name in child_directories
            if name not in EXCLUDED_DIRECTORIES and not name.startswith(".")
        )
        for filename in filenames:
            if filename.startswith("."):
                continue
            path = Path(directory, filename)
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                size = path.stat(follow_symlinks=False).st_size
            except OSError:
                skipped_entries += 1
                continue

            file_count += 1
            total_bytes += size
            extensions[path.suffix.lower() or "[no extension]"] += 1
            largest_files.append((size, path.relative_to(root).as_posix()))

    largest_files.sort(key=lambda item: (-item[0], item[1]))
    return {
        "root": root.name,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "by_extension": dict(sorted(extensions.items())),
        "largest_files": [
            {"path": path, "bytes": size} for size, path in largest_files[:5]
        ],
        "skipped_entries": skipped_entries,
    }


def main():
    root = Path.cwd()
    try:
        report = inventory(root)
    except OSError as error:
        print(f"Could not inspect workspace: {error}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2))
    return 1 if report["skipped_entries"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
