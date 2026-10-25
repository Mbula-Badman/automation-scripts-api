#!/usr/bin/env python3
"""Parse project Python files without executing them."""

import ast

from _project_utils import emit_report, project_files, relative_path


def main():
    files, errors = project_files()
    python_files = [path for path in files if path.suffix.lower() == ".py"]
    failures = []
    for path in python_files:
        try:
            source = path.read_text(encoding="utf-8-sig")
            ast.parse(source, filename=relative_path(path))
        except (OSError, SyntaxError, UnicodeError) as error:
            failures.append({"path": relative_path(path), "error": str(error)})

    report = {
        "checked_files": len(python_files),
        "syntax_errors": failures,
        "scan_errors": errors,
    }
    return emit_report(report, bool(failures or errors))


if __name__ == "__main__":
    raise SystemExit(main())
