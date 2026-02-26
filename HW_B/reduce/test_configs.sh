#!/usr/bin/env bash

set -e

# ---------------------------------------------------------------------------
# Reduce library test configurations
# ---------------------------------------------------------------------------
# kernel_x_dim >= 2, kernel_y_dim >= 1, extent >= 1, results_per_pe >= 1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configs: kernel_x_dim kernel_y_dim extent results_per_pe
configs=(
  # Minimal
  "2 1 1 1"
  "2 1 2 1"
  "2 1 1 2"

  # Two PEs, multiple rows
  "2 2 2 2"
  "2 3 4 2"

  # Three PEs (tests PSUM path)
  "3 1 2 1"
  "3 1 2 2"
  "3 2 4 3"

  # Four PEs (two middle PEs)
  "4 1 2 2"
  "4 2 2 1"
  "4 1 4 4"

  # Larger
  "5 1 2 2"
  "6 2 2 1"
  "3 3 3 3"
)

PASS=0
FAIL=0
ERRORS=()

for cfg in "${configs[@]}"; do
  read -r kx ky ext rpp <<< "$cfg"
  echo "========================================"
  echo "Testing kernel_x=$kx kernel_y=$ky extent=$ext results_per_pe=$rpp"
  echo "========================================"

  if ! "${SCRIPT_DIR}/run_test.sh" "$kx" "$ky" "$ext" "$rpp"; then
    echo "FAIL: kernel_x=$kx kernel_y=$ky extent=$ext results_per_pe=$rpp"
    FAIL=$((FAIL + 1))
    ERRORS+=("kernel_x=$kx kernel_y=$ky extent=$ext results_per_pe=$rpp")
    continue
  fi

  echo "PASS: kernel_x=$kx kernel_y=$ky extent=$ext results_per_pe=$rpp"
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
