#!/usr/bin/env bash

set -e

# ---------------------------------------------------------------------------
# Broadcast library test runner
# ---------------------------------------------------------------------------
# Usage: ./run_test.sh [sizeX] [sizeY] [N_per_pe] [--debug|--debug-instr]
#
# Constraints:
#   sizeY >= 2  (broadcast needs at least 2 PEs in the column)
#   sizeX >= 1
#   N_per_pe >= 1

if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
  echo "Usage: $0 [sizeX] [sizeY] [N_per_pe] [--debug|--debug-instr]"
  echo "  sizeX:    Width of PE grid  (default: 1)"
  echo "  sizeY:    Height of PE grid (default: 2, minimum 2)"
  echo "  N_per_pe: Elements per PE   (default: 4)"
  echo "  --debug:      Enable landing/router debug traces"
  echo "  --debug-instr: Enable instruction-level debug traces"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse positional parameters with defaults
sizeX=${1:-1}
sizeY=${2:-2}
N_per_pe=${3:-4}

# Parse debug flags
for arg in "$@"; do
  if [[ "$arg" == "--debug" ]]; then
    export APPTAINERENV_SIMFABRIC_DEBUG=landing,router
    export SIMFABRIC_DEBUG=landing,router
  elif [[ "$arg" == "--debug-instr" ]]; then
    export APPTAINERENV_SIMFABRIC_DEBUG=landing,router,inst_trace
    export SIMFABRIC_DEBUG=landing,router,inst_trace
  fi
done

# Clean output dir
rm -rf "${SCRIPT_DIR}/out"

echo "Running broadcast test: sizeX=$sizeX, sizeY=$sizeY, N_per_pe=$N_per_pe"

cslc --arch=wse2 "${SCRIPT_DIR}/test_layout.csl" \
  --fabric-dims=$(( (2 * 4) + $sizeX )),$(( (2 * 1) + $sizeY )) \
  --fabric-offsets=4,1 \
  --params=kernel_x_dim:${sizeX},kernel_y_dim:${sizeY},N_per_pe:${N_per_pe} \
  --params=MEMCPYH2D_DATA_1_ID:2 \
  --params=MEMCPYD2H_DATA_1_ID:4 \
  -o "${SCRIPT_DIR}/out" --memcpy --channels 1

cs_python "${SCRIPT_DIR}/run_test.py" --name "${SCRIPT_DIR}/out"
