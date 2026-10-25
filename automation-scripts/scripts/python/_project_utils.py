"""Shared safe project-file traversal and JSON output helpers."""

import json
import os
from pathlib import Path

EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def project_files(root=None):
    """Return visible regular files and traversal errors under the project root."""
    root = Path(root or Path.cwd()).resolve()
    files = []
    errors = []

    def record_walk_error(error):
        errors.append(str(error))

    for directory, child_directories, filenames in os.walk(
        root, topdown=True, onerror=record_walk_error, followlinks=False
    ):
        child_directories[:] = sorted(
            name
            for name in child_directories
            if name not in EXCLUDED_DIRECTORIES
            and not name.startswith(".")
            and not Path(directory, name).is_symlink()
        )
        for filename in filenames:
            if filename.startswith("."):
                continue
            path = Path(directory, filename)
            try:
                if not path.is_symlink() and path.is_file():
                    files.append(path)
            except OSError as error:
                errors.append(f"{path}: {error}")

    return sorted(files), errors


def relative_path(path, root=None):
    root = Path(root or Path.cwd()).resolve()
    return Path(path).relative_to(root).as_posix()


def emit_report(report, warning=False):
    report["status"] = "warning" if warning else "ok"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if warning else 0
