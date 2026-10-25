#!/usr/bin/env python3
"""Summarize requirements.txt entries without installing or resolving packages."""

import re
from pathlib import Path

from _project_utils import emit_report

REQUIREMENT = re.compile(
    r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(.*)$"
)


def main():
    manifest = Path.cwd() / "requirements.txt"
    if not manifest.is_file():
        return emit_report(
            {"manifest": "requirements.txt", "error": "File not found"},
            warning=True,
        )

    dependencies = []
    errors = []
    try:
        lines = manifest.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        return emit_report(
            {"manifest": "requirements.txt", "error": str(error)},
            warning=True,
        )

    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", ".")):
            continue
        match = REQUIREMENT.match(line)
        if not match:
            errors.append({"line": line_number, "text": raw_line})
            continue
        name, specifier = match.groups()
        dependencies.append(
            {
                "name": name,
                "specifier": specifier.strip(),
                "pinned": specifier.strip().startswith(("==", "===")),
            }
        )

    report = {
        "manifest": "requirements.txt",
        "dependency_count": len(dependencies),
        "pinned_count": sum(item["pinned"] for item in dependencies),
        "unpinned_count": sum(not item["pinned"] for item in dependencies),
        "dependencies": dependencies,
        "unparsed_lines": errors,
        "contacts_package_indexes": False,
    }
    return emit_report(report, bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
