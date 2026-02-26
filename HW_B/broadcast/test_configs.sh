#!/usr/bin/env bash

set -e

# ---------------------------------------------------------------------------
# Broadcast library test configurations
# ---------------------------------------------------------------------------
# Runs broadcast test across multiple grid sizes and element counts.
#
# Constraints:
#   sizeY >= 2
#   sizeX >= 1
#   N_per_pe >= 1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configs: sizeX sizeY N_per_pe
configs=(
  # Minimal: single column
  "1 2 1"
  "1 2 4"
  "1 3 4"
  "1 4 4"

  # Two columns (independent broadcasts)
  "2 2 1"
  "2 2 4"
  "2 3 4"
  "2 4 8"

  # Larger grids
  "1 8 8"
  "2 4 16"
  "1 3 1"
  "2 2 16"

  # Odd heights
  "1 3 3"
  "2 5 4"
  "1 7 2"
)

PASS=0
FAIL=0
ERRORS=()

for cfg in "${configs[@]}"; do
  read -r sizeX sizeY N_per_pe <<< "$cfg"
  echo "========================================"
  echo "Testing sizeX=$sizeX sizeY=$sizeY N_per_pe=$N_per_pe"
  echo "========================================"

  if ! "${SCRIPT_DIR}/run_test.sh" "$sizeX" "$sizeY" "$N_per_pe"; then
    echo "FAIL: sizeX=$sizeX sizeY=$sizeY N_per_pe=$N_per_pe"
    FAIL=$((FAIL + 1))
    ERRORS+=("sizeX=$sizeX sizeY=$sizeY N_per_pe=$N_per_pe")
    continue
  fi

  echo "PASS: sizeX=$sizeX sizeY=$sizeY N_per_pe=$N_per_pe"
  PASS=$((PASS + 1))
done

echo ""
echo "========================================"
echo "Results: $PASS passed, $FAIL failed out of ${#configs[@]} configs"
echo "========================================"
if [[ ${#ERRORS[@]} -gt 0 ]]; then
  echo "Failed configs:"
  for err in "${ERRORS[@]}"; do
    echo "  $err"
  done
  exit 1
fi
