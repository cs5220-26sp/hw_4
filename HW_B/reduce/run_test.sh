#!/usr/bin/env bash

set -e

# ---------------------------------------------------------------------------
# Reduce library test runner
# ---------------------------------------------------------------------------
# Usage: ./run_test.sh [kernel_x_dim] [kernel_y_dim] [extent] [results_per_pe]
#
# Constraints:
#   kernel_x_dim >= 2
#   kernel_y_dim >= 1
#   extent >= 1
#   results_per_pe >= 1

if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
  echo "Usage: $0 [kernel_x_dim] [kernel_y_dim] [extent] [results_per_pe]"
  echo "  kernel_x_dim:   PEs in reduction direction (default: 2, min 2)"
  echo "  kernel_y_dim:   Independent rows            (default: 1)"
  echo "  extent:         Vector length per reduction  (default: 2)"
  echo "  results_per_pe: Results landing on each PE   (default: 2)"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kernel_x_dim=${1:-2}
kernel_y_dim=${2:-1}
extent=${3:-2}
results_per_pe=${4:-2}

rm -rf "${SCRIPT_DIR}/out"

echo "Running reduce test: kernel_x_dim=$kernel_x_dim, kernel_y_dim=$kernel_y_dim, extent=$extent, results_per_pe=$results_per_pe"

cslc --arch=wse2 "${SCRIPT_DIR}/test_layout.csl" \
  --fabric-dims=$(( (2 * 4) + kernel_x_dim )),$(( (2 * 1) + kernel_y_dim )) \
  --fabric-offsets=4,1 \
  --params=kernel_x_dim:${kernel_x_dim},kernel_y_dim:${kernel_y_dim},extent:${extent},results_per_pe:${results_per_pe} \
  --params=MEMCPYH2D_DATA_1_ID:2 \
  --params=MEMCPYD2H_DATA_1_ID:4 \
  --max-inlined-iterations 150 \
  -o "${SCRIPT_DIR}/out" --memcpy --channels 1

cs_python "${SCRIPT_DIR}/run_test.py" --name "${SCRIPT_DIR}/out"
