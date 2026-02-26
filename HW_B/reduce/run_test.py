#!/usr/bin/env cs_python

"""
Test runner for the row reduction library.

Each PE(x, y) gets unique send data.  After reduction, PE(x) should hold
the sum of all PEs' contributions for the rounds assigned to it.

Round-to-PE mapping: PE x receives results for rounds
    [x * results_per_pe .. (x+1) * results_per_pe - 1].
"""

import argparse
import json
import sys

import numpy as np

from cerebras.sdk.runtime.sdkruntimepybind import SdkRuntime, MemcpyDataType, MemcpyOrder  # pylint: disable=no-name-in-module

parser = argparse.ArgumentParser()
parser.add_argument('--name', help="the test compile output dir")
parser.add_argument('--cmaddr', help="IP:port for CS system")
args = parser.parse_args()

with open(f"{args.name}/out.json", encoding='utf-8') as f:
    compile_data = json.load(f)

kernel_x_dim   = int(compile_data['params']['kernel_x_dim'])
kernel_y_dim   = int(compile_data['params']['kernel_y_dim'])
extent         = int(compile_data['params']['extent'])
results_per_pe = int(compile_data['params']['results_per_pe'])

n_reductions = results_per_pe * kernel_x_dim
send_size    = n_reductions * extent       # per PE
result_size  = results_per_pe * extent     # per PE

print(f"Reduce test: X={kernel_x_dim}, Y={kernel_y_dim}, "
      f"extent={extent}, results_per_pe={results_per_pe}")
print(f"  n_reductions={n_reductions}, send_size={send_size}, "
      f"result_size={result_size}")

# -----------------------------------------------------------------------
# Create runner
# -----------------------------------------------------------------------

runner = SdkRuntime(args.name, cmaddr=args.cmaddr, suppress_simfab_trace=True)
send_sym   = runner.get_id('send_buf')
result_sym = runner.get_id('result')

runner.load()
runner.run()

# -----------------------------------------------------------------------
# Generate and load send data
# -----------------------------------------------------------------------
# send_data[y, x, r*extent+i] — use small integers for exact float32
# Pattern: value = y * 10000 + r * 100 + x * 10 + i + 1

send_data = np.zeros((kernel_y_dim, kernel_x_dim, send_size), dtype=np.float32)
for py in range(kernel_y_dim):
    for px in range(kernel_x_dim):
        for r in range(n_reductions):
            for i in range(extent):
                send_data[py, px, r * extent + i] = float(
                    py * 10000 + r * 100 + px * 10 + i + 1
                )

print("\nSend data (first PE per row):")
for py in range(kernel_y_dim):
    print(f"  PE(0,{py}): {send_data[py, 0, :min(8, send_size)]}...")

runner.memcpy_h2d(send_sym, send_data.ravel(), 0, 0,
                  kernel_x_dim, kernel_y_dim, send_size,
                  streaming=False, order=MemcpyOrder.ROW_MAJOR,
                  data_type=MemcpyDataType.MEMCPY_32BIT, nonblock=False)

# -----------------------------------------------------------------------
# Launch reduction
# -----------------------------------------------------------------------

print("\nLaunching reduction...")
runner.launch('f_reduce', nonblock=False)
print("Reduction complete.")

# -----------------------------------------------------------------------
# Read back results
# -----------------------------------------------------------------------

result_flat = np.zeros(kernel_x_dim * kernel_y_dim * result_size,
                       dtype=np.float32)
runner.memcpy_d2h(result_flat, result_sym, 0, 0,
                  kernel_x_dim, kernel_y_dim, result_size,
                  streaming=False, order=MemcpyOrder.ROW_MAJOR,
                  data_type=MemcpyDataType.MEMCPY_32BIT, nonblock=False)

runner.stop()

result_data = result_flat.reshape(kernel_y_dim, kernel_x_dim, result_size)

# -----------------------------------------------------------------------
# Verify
# -----------------------------------------------------------------------
# PE(x, y) should hold results for rounds [x*rpp .. (x+1)*rpp - 1]
# result[j*extent+i] = sum over x' of send_data[y, x', round*extent+i]
#   where round = x * results_per_pe + j

print("\nVerification:")
all_pass = True
for py in range(kernel_y_dim):
    for px in range(kernel_x_dim):
        expected = np.zeros(result_size, dtype=np.float32)
        for j in range(results_per_pe):
            round_r = px * results_per_pe + j
            for i in range(extent):
                total = 0.0
                for src_x in range(kernel_x_dim):
                    total += send_data[py, src_x, round_r * extent + i]
                expected[j * extent + i] = total

        actual = result_data[py, px]
        match = np.allclose(actual, expected, atol=1e-4, rtol=1e-5)
        status = "PASS" if match else "FAIL"
        print(f"  PE({px},{py}): {status}")
        if not match:
            all_pass = False
            print(f"    Expected: {expected}")
            print(f"    Actual:   {actual}")

if all_pass:
    print("\nSUCCESS: All PEs received correct reduction results!")
else:
    print("\nFAILURE: Some PEs have incorrect data!")
    sys.exit(1)
