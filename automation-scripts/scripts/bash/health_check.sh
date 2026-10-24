#!/usr/bin/env bash
# health_check.sh - Quick system health report for Linux machines.
# Exit codes: 0 = healthy, 1 = a threshold was exceeded, 2 = bad usage.

set -u

DISK_LIMIT=85   # percent
MEM_LIMIT=90    # percent
LOAD_LIMIT=""   # defaults to number of CPU cores
JSON=0
SERVICES=()

usage() {
  cat << USAGE
Usage: $(basename "$0") [options]

Options:
  -d PERCENT   Disk usage warning threshold (default: $DISK_LIMIT)
  -m PERCENT   Memory usage warning threshold (default: $MEM_LIMIT)
  -l LOAD      1-min load warning threshold (default: number of CPU cores)
  -s SERVICE   systemd service to check (repeatable), e.g. -s ssh -s cron
  -j           Output JSON (for the dashboard / database)
  -h           Show this help
USAGE
}

while getopts "d:m:l:s:jh" opt; do
  case "$opt" in
    d) DISK_LIMIT="$OPTARG" ;;
    m) MEM_LIMIT="$OPTARG" ;;
    l) LOAD_LIMIT="$OPTARG" ;;
    s) SERVICES+=("$OPTARG") ;;
    j) JSON=1 ;;
    h) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

CORES=$(nproc 2>/dev/null || echo 1)
LOAD_LIMIT=${LOAD_LIMIT:-$CORES}

HOST=$(hostname)
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
UPTIME=$(uptime -p 2>/dev/null | sed 's/^up //')
LOAD1=$(cut -d' ' -f1 /proc/loadavg)

read -r MEM_TOTAL MEM_USED < <(free -m | awk '/^Mem:/ {print $2, $3}')
MEM_PCT=$(( MEM_USED * 100 / MEM_TOTAL ))

# Disk usage per real filesystem: "mount:percent"
mapfile -t DISKS < <(df -hP -x tmpfs -x devtmpfs -x squashfs -x overlay 2>/dev/null \
  | awk 'NR>1 {gsub("%","",$5); print $6":"$5}')

ALERTS=()

(( MEM_PCT >= MEM_LIMIT )) && ALERTS+=("Memory at ${MEM_PCT}% (limit ${MEM_LIMIT}%)")
awk -v l="$LOAD1" -v t="$LOAD_LIMIT" 'BEGIN{exit !(l>=t)}' \
  && ALERTS+=("Load ${LOAD1} (limit ${LOAD_LIMIT})")

for d in "${DISKS[@]}"; do
  mount="${d%%:*}"; pct="${d##*:}"
  (( pct >= DISK_LIMIT )) && ALERTS+=("Disk ${mount} at ${pct}% (limit ${DISK_LIMIT}%)")
done

SVC_STATUS=()
for s in "${SERVICES[@]:-}"; do
  [[ -z "$s" ]] && continue
  if command -v systemctl > /dev/null 2>&1; then
    state=$(systemctl is-active "$s" 2>/dev/null || true)
    [[ -z "$state" ]] && state="unknown"
  else
    state="unknown"
  fi
  SVC_STATUS+=("${s}:${state}")
  [[ "$state" != "active" ]] && ALERTS+=("Service ${s} is ${state}")
done

STATUS="ok"
(( ${#ALERTS[@]} > 0 )) && STATUS="warning"

if (( JSON )); then
  printf '{\n'
  printf '  "host": "%s",\n  "timestamp": "%s",\n  "status": "%s",\n' "$HOST" "$TS" "$STATUS"
  printf '  "uptime": "%s",\n  "load_1min": %s,\n  "cpu_cores": %s,\n' "$UPTIME" "$LOAD1" "$CORES"
  printf '  "memory": {"used_mb": %s, "total_mb": %s, "percent": %s},\n' "$MEM_USED" "$MEM_TOTAL" "$MEM_PCT"
  printf '  "disks": ['
  first=1
  for d in "${DISKS[@]}"; do
    (( first )) || printf ', '; first=0
    printf '{"mount": "%s", "percent": %s}' "${d%%:*}" "${d##*:}"
  done
  printf '],\n  "services": ['
  first=1
  for s in "${SVC_STATUS[@]:-}"; do
    [[ -z "$s" ]] && continue
    (( first )) || printf ', '; first=0
    printf '{"name": "%s", "state": "%s"}' "${s%%:*}" "${s##*:}"
  done
  printf '],\n  "alerts": ['
  first=1
  for a in "${ALERTS[@]:-}"; do
    [[ -z "$a" ]] && continue
    (( first )) || printf ', '; first=0
    printf '"%s"' "$a"
  done
  printf ']\n}\n'
else
  echo "=== System Health: $HOST ($TS) ==="
  echo "Uptime : $UPTIME"
  echo "Load   : $LOAD1 (cores: $CORES)"
  echo "Memory : ${MEM_USED}MB / ${MEM_TOTAL}MB (${MEM_PCT}%)"
  echo "Disks  :"
  for d in "${DISKS[@]}"; do printf '  %-20s %s%%\n' "${d%%:*}" "${d##*:}"; done
  if (( ${#SVC_STATUS[@]} > 0 )); then
    echo "Services:"
    for s in "${SVC_STATUS[@]}"; do printf '  %-20s %s\n' "${s%%:*}" "${s##*:}"; done
  fi
  echo "-----------------------------------------"
  if (( ${#ALERTS[@]} == 0 )); then
    echo "STATUS: OK"
  else
    echo "STATUS: WARNING"
    for a in "${ALERTS[@]}"; do echo "  ! $a"; done
  fi
fi

[[ "$STATUS" == "ok" ]] && exit 0 || exit 1
