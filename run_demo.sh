#!/bin/bash
# Launch the HCVRP delivery simulator.
#
# Not a SLURM job: this is an interactive web app, and one instance solves on
# CPU in well under a second per method, so it runs on the login node. Forward
# the port from your laptop first:
#
#     ssh -L 8000:localhost:8000 athota@master
#
# then run this on the cluster and open http://127.0.0.1:8000 locally.

set -euo pipefail
cd "$(dirname "$0")"

PORT="${1:-8000}"

if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "note: no .venv here — using whatever python is on PATH"
fi

echo "=========================================================="
echo " Pre-flight: verifying the checkpoints and the route maths"
echo "=========================================================="
if python demo/selftest.py; then
  echo
else
  echo
  echo "Self-test failed. Starting anyway so you can still look at the UI,"
  echo "but treat any numbers on screen as untrustworthy until it passes."
  echo "To run without the models at all:  python demo/server.py --mock"
  echo
fi

echo "=========================================================="
echo " Serving on port ${PORT}"
echo "=========================================================="
exec python -u demo/server.py --port "${PORT}"
