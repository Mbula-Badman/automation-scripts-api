#!/usr/bin/env python3
"""log_analyzer.py - Detect SSH brute-force attempts in Linux auth logs.

Reads an auth log (e.g. /var/log/auth.log), counts failed logins per source
IP, and flags IPs that reach a threshold.

Exit codes: 0 = nothing suspicious, 1 = suspicious IPs found, 2 = error.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict

# "Failed password for [invalid user] NAME from 1.2.3.4 port 22 ssh2"
FAILED_RE = re.compile(
    r"Failed (?:password|publickey) for (?:invalid user )?(?P<user>\S+) "
    r"from (?P<ip>[0-9a-fA-F:.]+)"
)
# "Invalid user NAME from 1.2.3.4"
INVALID_RE = re.compile(r"Invalid user (?P<user>\S+) from (?P<ip>[0-9a-fA-F:.]+)")
ACCEPTED_RE = re.compile(
    r"Accepted (?:password|publickey) for (?P<user>\S+) from (?P<ip>[0-9a-fA-F:.]+)"
)


def analyze(path):
    failures = Counter()
    users_tried = defaultdict(set)
    accepted_after_fail = set()
    accepted = []

    with open(path, "r", errors="replace") as fh:
        for line in fh:
            m = FAILED_RE.search(line) or INVALID_RE.search(line)
            if m:
                failures[m["ip"]] += 1
                users_tried[m["ip"]].add(m["user"])
                continue
            a = ACCEPTED_RE.search(line)
            if a:
                accepted.append((a["user"], a["ip"]))
                if a["ip"] in failures:
                    accepted_after_fail.add(a["ip"])

    return failures, users_tried, accepted_after_fail


def main():
    p = argparse.ArgumentParser(description="Flag SSH brute-force attempts in an auth log.")
    p.add_argument("logfile", help="Path to auth log, e.g. /var/log/auth.log")
    p.add_argument("-t", "--threshold", type=int, default=5,
                   help="Failed attempts needed to flag an IP (default: 5)")
    p.add_argument("--json", action="store_true", help="Output JSON")
    args = p.parse_args()

    try:
        failures, users_tried, compromised = analyze(args.logfile)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    flagged = [
        {
            "ip": ip,
            "failed_attempts": n,
            "usernames_tried": sorted(users_tried[ip]),
            "later_logged_in": ip in compromised,
        }
        for ip, n in failures.most_common()
        if n >= args.threshold
    ]

    if args.json:
        print(json.dumps({
            "total_failed": sum(failures.values()),
            "unique_ips": len(failures),
            "threshold": args.threshold,
            "flagged": flagged,
        }, indent=2))
    else:
        print(f"Total failed attempts : {sum(failures.values())}")
        print(f"Unique source IPs     : {len(failures)}")
        print(f"Threshold             : {args.threshold}\n")
        if not flagged:
            print("No suspicious IPs found.")
        else:
            print(f"{'IP':<18}{'FAILS':<8}{'USERS':<8}NOTE")
            for f in flagged:
                note = "!! successful login after failures" if f["later_logged_in"] else ""
                print(f"{f['ip']:<18}{f['failed_attempts']:<8}{len(f['usernames_tried']):<8}{note}")

    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
