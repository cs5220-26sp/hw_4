#!/usr/bin/env python3
"""Submit HW4 leaderboard results to the CS5220 leaderboard server."""

import re
import sys
import urllib.request
import json

LEADERBOARD_URL = "https://leaderboard-zm07.onrender.com/api/hw4/submit"
HEADER = "===== CS5220 HW4 LEADERBOARD SUBMISSION ====="
FOOTER = "===== END CS5220 HW4 LEADERBOARD SUBMISSION ====="

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output-file>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        raw = f.read()

    # Check that correctness tests passed (submission block present)
    if HEADER not in raw:
        print("ERROR: Submission header not found in output file.")
        print("This means the correctness tests (test_configs.sh) likely failed.")
        print("Fix your implementation and re-run job-leaderboard before submitting.")
        sys.exit(1)

    if FOOTER not in raw:
        print("ERROR: Submission footer not found in output file.")
        print("The job may not have completed successfully.")
        sys.exit(1)

    # Extract the submission block
    start = raw.index(HEADER)
    end = raw.index(FOOTER) + len(FOOTER)
    submission = raw[start:end]

    # Parse and display the runtime for confirmation
    name_match = re.search(r"LEADERBOARD_NAME:\s*(\S+)", submission)
    name = name_match.group(1) if name_match else "unknown"

    perf_match = re.search(r"--- PERF ---\n(.*?)--- END PERF ---", submission, re.DOTALL)
    runtime = None
    if perf_match:
        max_match = re.search(r"Max:\s+([\d]+)", perf_match.group(1))
        if max_match:
            runtime = int(max_match.group(1))

    print(f"Name:    {name}")
    if runtime is not None:
        print(f"Runtime: {runtime:,} cycles")
    else:
        print("WARNING: Could not parse Runtime from output.")

    # Submit
    print(f"\nSubmitting to {LEADERBOARD_URL} ...")
    req = urllib.request.Request(
        LEADERBOARD_URL,
        data=submission.encode("utf-8"),
        headers={"Content-Type": "text/plain"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"Success! Submitted as: {result.get('name', name)}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: Server returned {e.code}: {body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Could not reach server: {e.reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
