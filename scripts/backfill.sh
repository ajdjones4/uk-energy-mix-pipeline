#!/usr/bin/env bash
start=${1:-2026-10-01}
end=${2:-$(date -I)}

d=$start
failed=()

while [[ "$d" < "$end" ]]; do
    if ! uv run python -m uk_energy_mix.ingest.carbon_intensity "$d"; then
    failed+=("$d")
    fi
    sleep 5 
    d=$(date -I -d "$d + 1 day")
done

if (( ${#failed[@]} )); then
      echo "Failed dates: ${failed[@]}"
      exit 1
  fi