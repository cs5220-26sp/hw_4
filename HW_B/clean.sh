#!/bin/bash

echo "Cleaning up old outputs and logs..."

# Clean test directories
for dir in "./broadcast" "./reduce" "."; do
  if [[ -d "$dir" ]]; then
    rm -rf "${dir}/out" "${dir}"/sim*.log "${dir}"/wio_* "${dir}"/simfab_traces "${dir}"/sim_stats.json "${dir}"/simconfig.json 2>/dev/null || true
  fi
done