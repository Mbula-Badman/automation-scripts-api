#!/usr/bin/env python3
"""Find TODO, FIXME, and XXX markers in project source files."""

import re

from _project_utils import emit_report, project_files, relative_path

SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".css", ".go", ".h", ".html", ".java", ".js",
    ".jsx", ".md", ".php", ".py", ".rb", ".rs", ".sh", ".sql", ".ts",
    ".tsx", ".xml", ".yaml", ".yml",
}
MARKER = re.compile(r"\b(TODO|FIXME|XXX)\b", re.IGNORECASE)
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_RESULTS = 100


def main():
    files, errors = project_files()
    matches = []
    skipped_large_files = 0
    for path in files:
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                skipped_large_files += 1
                continue
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1
            ):
                if MARKER.search(line):
                    matches.append(
                        {"path": relative_path(path), "line": line_number, "text": line.strip()[:200]}
                    )
                    if len(matches) >= MAX_RESULTS:
                        break
        except OSError as error:
            errors.append(f"{relative_path(path)}: {error}")
        if len(matches) >= MAX_RESULTS:
            break

    report = {
        "matches": matches,
        "result_limit": MAX_RESULTS,
        "limit_reached": len(matches) >= MAX_RESULTS,
        "skipped_large_files": skipped_large_files,
        "scan_errors": errors,
    }
    return emit_report(report, bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
