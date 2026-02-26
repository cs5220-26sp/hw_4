#!/usr/bin/env cs_python

"""
Test runner for the column broadcast library.

Loads unique data into each PE's send buffer, launches the broadcast, reads
back the receive buffer, and verifies that every PE in a column received the
correct concatenation of all senders' data.
"""

import argparse
import json
import sys

import numpy as np

from cerebras.sdk.runtime.sdkruntimepybind import SdkRuntime, MemcpyDataType, MemcpyOrder  # pylint: disable=no-name-in-module

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('--name', help="the test compile output dir")
parser.add_argument('--cmaddr', help="IP:port for CS system")
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Read compile-time parameters
# ---------------------------------------------------------------------------

with open(f"{args.name}/out.json", encoding='utf-8') as f:
    compile_data = json.load(f)

kernel_x_dim = int(compile_data['params']['kernel_x_dim'])
kernel_y_dim = int(compile_data['params']['kernel_y_dim'])
N_per_pe     = int(compile_data['params']['N_per_pe'])

result_size = N_per_pe * kernel_y_dim  # elements per PE in the result buffer

print(f"Broadcast test: X={kernel_x_dim}, Y={kernel_y_dim}, N_per_pe={N_per_pe}")
print(f"  Each PE sends {N_per_pe} elements, receives {result_size} elements")

# ---------------------------------------------------------------------------
# Create runner
# ---------------------------------------------------------------------------

runner = SdkRuntime(args.name, cmaddr=args.cmaddr, suppress_simfab_trace=True)

send_sym   = runner.get_id('send_buf')
result_sym = runner.get_id('result')

runner.load()
runner.run()

# ---------------------------------------------------------------------------
# Generate and load send data
# ---------------------------------------------------------------------------

# Each PE(x, y) gets a unique pattern:
#   send_data[y, x, i] = y * 1000.0 + x * 100.0 + i
# This makes it trivial to identify which PE produced which data.

send_data = np.zeros((kernel_y_dim, kernel_x_dim, N_per_pe), dtype=np.float32)
for py in range(kernel_y_dim):
    for px in range(kernel_x_dim):
        base = py * 1000.0 + px * 100.0
        send_data[py, px] = np.arange(base, base + N_per_pe, dtype=np.float32)

print("\nSend data per PE:")
for py in range(kernel_y_dim):
    for px in range(kernel_x_dim):
        print(f"  PE({px},{py}): {send_data[py, px]}")

# Copy to device (H2D)
send_prepared = send_data.ravel()
runner.memcpy_h2d(send_sym, send_prepared, 0, 0, kernel_x_dim, kernel_y_dim,
                  N_per_pe, streaming=False, order=MemcpyOrder.ROW_MAJOR,
                  data_type=MemcpyDataType.MEMCPY_32BIT, nonblock=False)

# ---------------------------------------------------------------------------
# Launch broadcast
# ---------------------------------------------------------------------------

print("\nLaunching broadcast...")
runner.launch('f_broadcast', nonblock=False)
print("Broadcast complete.")

# ---------------------------------------------------------------------------
# Read back results (D2H)
# ---------------------------------------------------------------------------

result_flat = np.zeros(kernel_x_dim * kernel_y_dim * result_size, dtype=np.float32)
runner.memcpy_d2h(result_flat, result_sym, 0, 0, kernel_x_dim, kernel_y_dim,
                  result_size, streaming=False, order=MemcpyOrder.ROW_MAJOR,
                  data_type=MemcpyDataType.MEMCPY_32BIT, nonblock=False)

runner.stop()

# Reshape: (kernel_y_dim, kernel_x_dim, result_size)
result_data = result_flat.reshape(kernel_y_dim, kernel_x_dim, result_size)

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

# Each PE(x, y) should have received, in order:
#   PE(x, 0) data || PE(x, 1) data || ... || PE(x, kernel_y_dim-1) data
# i.e. all senders from the same column x.

print("\nVerification:")
all_pass = True
for py in range(kernel_y_dim):
    for px in range(kernel_x_dim):
        # Build expected result for PE(px, py)
        expected = np.concatenate(
            [send_data[src_y, px] for src_y in range(kernel_y_dim)]
        )
        actual = result_data[py, px]

        match = np.allclose(actual, expected, atol=1e-6, rtol=0)
        status = "PASS" if match else "FAIL"
        print(f"  PE({px},{py}): {status}")
        if not match:
            all_pass = False
            print(f"    Expected: {expected}")
            print(f"    Actual:   {actual}")

if all_pass:
    print("\nSUCCESS: All PEs received correct broadcast data!")
else:
    print("\nFAILURE: Some PEs have incorrect data!")
    sys.exit(1)
