#!/usr/bin/env python3
"""Cross-platform system health reporter.

This keeps the original health_check.sh intent but runs in environments where
bash/systemd is unavailable, such as a plain Windows host or a minimal Linux
container.
"""

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone


def run_command(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, check=False)
    except OSError:
        return None


def get_host():
    return socket.gethostname()


def get_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_uptime():
    if shutil.which("uptime"):
        proc = run_command(["uptime", "-p"])
        if proc and proc.stdout.strip():
            return proc.stdout.strip().replace("up ", "")

    if os.path.exists("/proc/uptime"):
        try:
            with open("/proc/uptime", "r", encoding="utf-8") as fh:
                seconds = float(fh.read().split()[0])
            days, remainder = divmod(seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)
            parts = []
            if days:
                parts.append(f"{int(days)} day{'s' if days != 1 else ''}")
            if hours:
                parts.append(f"{int(hours)} hour{'s' if hours != 1 else ''}")
            if minutes or not parts:
                parts.append(f"{int(minutes)} minute{'s' if minutes != 1 else ''}")
            return ", ".join(parts)
        except (OSError, ValueError):
            pass

    if platform.system() == "Windows":
        proc = run_command(["wmic", "os", "get", "lastbootuptime"])
        if proc and proc.stdout:
            lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            for line in lines[1:]:
                if line.startswith("202"):
                    boot = line
                    break
            else:
                boot = None
            if boot:
                try:
                    dt = datetime.strptime(boot, "%Y%m%d%H%M%S.000000+000")
                    return f"{(datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)).total_seconds() / 3600:.1f} hours"
                except ValueError:
                    pass

    return "unknown"


def get_cpu_cores():
    return os.cpu_count() or 1


def get_load_1min():
    try:
        with open("/proc/loadavg", "r", encoding="utf-8") as fh:
            return float(fh.read().split()[0])
    except OSError:
        return None


def get_memory_usage():
    if os.path.exists("/proc/meminfo"):
        try:
            meminfo = {}
            with open("/proc/meminfo", "r", encoding="utf-8") as fh:
                for line in fh:
                    parts = line.strip().split(":", 1)
                    if len(parts) != 2:
                        continue
                    key, value = parts
                    try:
                        meminfo[key] = int(value.strip().split()[0])
                    except ValueError:
                        continue
            total = meminfo.get("MemTotal", 0)
            available = meminfo.get("MemAvailable")
            if available is None:
                available = meminfo.get("MemFree", 0)
            used = max(total - available, 0)
            percent = int((used * 100) / total) if total else 0
            return total, used, percent
        except (OSError, ValueError):
            pass

    if platform.system() == "Windows":
        proc = run_command(["wmic", "os", "get", "TotalVisibleMemorySize,FreePhysicalMemory", "/value"])
        if proc and proc.stdout:
            values = {}
            for line in proc.stdout.splitlines():
                if "=" not in line:
                    continue
                key, value = [part.strip() for part in line.split("=", 1)]
                if key and value:
                    values[key] = value
            total = int(values.get("TotalVisibleMemorySize", 0) or 0)
            free = int(values.get("FreePhysicalMemory", 0) or 0)
            used = max(total - free, 0)
            percent = int((used * 100) / total) if total else 0
            if total > 0:
                return total, used, percent

    return 0, 0, 0


def list_disks():
    if platform.system() == "Windows":
        drive = os.getcwd().split(":")[0] + ":\\" if ":" in os.getcwd() else "C:\\"
        total, used, _ = shutil.disk_usage(drive)
        percent = int((used * 100) / total) if total else 0
        return [{"mount": drive, "percent": percent}]

    total, used, _ = shutil.disk_usage("/")
    percent = int((used * 100) / total) if total else 0
    return [{"mount": "/", "percent": percent}]


def get_service_state(service_name):
    if shutil.which("systemctl"):
        proc = run_command(["systemctl", "is-active", service_name])
        if proc is not None:
            state = (proc.stdout or proc.stderr or "").strip() or "unknown"
            return state if state else "unknown"

    if platform.system() == "Windows":
        proc = run_command(["sc", "query", service_name])
        if proc is not None:
            output = proc.stdout or proc.stderr or ""
            state = "unknown"
            for line in output.splitlines():
                if "STATE" in line.upper() and ":" in line:
                    if "RUNNING" in line.upper():
                        state = "running"
                        break
                    if "STOPPED" in line.upper():
                        state = "stopped"
                        break
            return state

    return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Quick system health report")
    parser.add_argument("-d", "--disk-limit", type=int, default=85, help="Disk usage warning threshold")
    parser.add_argument("-m", "--mem-limit", type=int, default=90, help="Memory usage warning threshold")
    parser.add_argument("-l", "--load-limit", type=int, default=None, help="Load warning threshold")
    parser.add_argument("-s", "--service", action="append", default=[], help="Service to check (repeatable)")
    parser.add_argument("-j", "--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    cores = get_cpu_cores()
    load_limit = args.load_limit if args.load_limit is not None else cores
    load_1min = get_load_1min()

    total_mb, used_mb, mem_percent = get_memory_usage()
    disks = list_disks()
    service_status = []
    alerts = []

    if used_mb and total_mb:
        if mem_percent >= args.mem_limit:
            alerts.append(f"Memory at {mem_percent}% (limit {args.mem_limit}%)")
    else:
        mem_percent = 0

    if load_1min is not None and load_1min >= load_limit:
        alerts.append(f"Load {load_1min} (limit {load_limit})")

    for item in disks:
        mount = item["mount"]
        percent = item["percent"]
        if percent >= args.disk_limit:
            alerts.append(f"Disk {mount} at {percent}% (limit {args.disk_limit}%)")

    for service_name in args.service:
        state = get_service_state(service_name)
        service_status.append({"name": service_name, "state": state})
        if state != "active" and state != "running":
            alerts.append(f"Service {service_name} is {state}")

    status = "ok" if not alerts else "warning"
    host = get_host()
    ts = get_timestamp()
    uptime = get_uptime()

    if args.json:
        payload = {
            "host": host,
            "timestamp": ts,
            "status": status,
            "uptime": uptime,
            "load_1min": load_1min,
            "cpu_cores": cores,
            "memory": {"used_mb": used_mb // 1024, "total_mb": total_mb // 1024, "percent": mem_percent},
            "disks": disks,
            "services": service_status,
            "alerts": alerts,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"=== System Health: {host} ({ts}) ===")
        print(f"Uptime : {uptime}")
        print(f"Load   : {load_1min if load_1min is not None else 'n/a'} (cores: {cores})")
        print(f"Memory : {used_mb // 1024}MB / {total_mb // 1024}MB ({mem_percent}%)")
        print("Disks  :")
        for item in disks:
            print(f"  {item['mount']:<20} {item['percent']}%")
        if service_status:
            print("Services:")
            for service in service_status:
                print(f"  {service['name']:<20} {service['state']}")
        print("-----------------------------------------")
        if not alerts:
            print("STATUS: OK")
        else:
            print("STATUS: WARNING")
            for alert in alerts:
                print(f"  ! {alert}")

    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
