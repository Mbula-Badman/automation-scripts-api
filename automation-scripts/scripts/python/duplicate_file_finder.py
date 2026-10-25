#!/usr/bin/env python3
"""Find identical project files by size and SHA-256 without deleting them."""

import hashlib
from collections import defaultdict

from _project_utils import emit_report, project_files, relative_path

MAX_HASH_BYTES = 100 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    files, errors = project_files()
    by_size = defaultdict(list)
    skipped_large_files = 0
    for path in files:
        try:
            size = path.stat().st_size
        except OSError as error:
            errors.append(f"{relative_path(path)}: {error}")
            continue
        if size > MAX_HASH_BYTES:
            skipped_large_files += 1
            continue
        by_size[size].append(path)

    by_digest = defaultdict(list)
    for same_size_files in by_size.values():
        if len(same_size_files) < 2:
            continue
        for path in same_size_files:
            try:
                by_digest[(path.stat().st_size, digest_file(path))].append(path)
            except OSError as error:
                errors.append(f"{relative_path(path)}: {error}")

    duplicates = [
        {
            "bytes": size,
            "sha256": digest,
            "paths": sorted(relative_path(path) for path in paths),
        }
        for (size, digest), paths in by_digest.items()
        if len(paths) > 1
    ]
    duplicates.sort(key=lambda item: item["paths"][0])
    report = {
        "duplicate_groups": duplicates,
        "duplicate_group_count": len(duplicates),
        "skipped_files_over_100_mib": skipped_large_files,
        "scan_errors": errors,
        "deletes_nothing": True,
    }
    return emit_report(report, bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
