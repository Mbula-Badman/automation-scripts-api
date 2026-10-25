#!/usr/bin/env python3
"""Report basic Python and operating-system details as JSON."""

import json
import os
import platform


def main():
    report = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "operating_system": platform.system(),
        "operating_system_release": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
