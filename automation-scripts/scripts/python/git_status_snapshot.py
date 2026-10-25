#!/usr/bin/env python3
"""Read the current local Git branch and working-tree status."""

import subprocess
from pathlib import Path

from _project_utils import emit_report


def main():
    root = Path.cwd()
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return emit_report(
            {"repository": str(root), "error": str(error)},
            warning=True,
        )

    if result.returncode:
        return emit_report(
            {
                "repository": str(root),
                "error": result.stderr.strip() or "Git status failed",
                "is_git_repository": False,
            },
            warning=True,
        )

    lines = result.stdout.splitlines()
    branch = lines[0][3:] if lines and lines[0].startswith("## ") else "unknown"
    report = {
        "repository": str(root),
        "is_git_repository": True,
        "branch": branch,
        "changes": lines[1:],
        "change_count": max(len(lines) - 1, 0),
    }
    return emit_report(report)


if __name__ == "__main__":
    raise SystemExit(main())
