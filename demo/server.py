"""Local web server for the HCVRP delivery demo.

Standard library only -- no Flask, no FastAPI -- so it adds nothing to the
cluster virtualenv and starts anywhere Python runs.

    python demo/server.py                 # real checkpoints if importable
    python demo/server.py --mock          # heuristic only, no torch needed
    python demo/server.py --port 8080 --runs-root <dir>

Then open http://127.0.0.1:8000. On the cluster, forward the port first:

    ssh -L 8000:localhost:8000 athota@master
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenarios                                      # noqa: E402
from backends import (                                 # noqa: E402
    CompositeBackend, DEFAULT_RUNS_ROOT, resolve_runs_root,
)
from routes import validity                           # noqa: E402

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
BACKEND: CompositeBackend | None = None
MAX_BODY = 4 * 1024 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = "HCVRPDemo/1.0"

    # ---------------------------------------------------------------- utils
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code: int, payload: dict):
        self._send(code, json.dumps(payload).encode("utf-8"), "application/json")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        if n > MAX_BODY:
            raise ValueError("request body too large")
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def log_message(self, fmt, *args):      # quieter console
        if "/api/" in (self.path or ""):
            sys.stderr.write("  %s %s\n" % (self.command, self.path))

    # ------------------------------------------------------------------ GET
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return self._file(os.path.join(STATIC, "index.html"))
        if path == "/api/methods":
            return self._json(200, {
                "methods": BACKEND.describe(),
                "backend": "torch" if BACKEND.torch else "heuristic-only",
                "reason": BACKEND.reason,
                "layouts": {k: v[0] for k, v in scenarios.LAYOUTS.items()},
                "train": scenarios.TRAIN,
            })
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            target = os.path.normpath(os.path.join(STATIC, rel))
            if not target.startswith(STATIC):          # no traversal
                return self._json(403, {"error": "forbidden"})
            return self._file(target)
        return self._json(404, {"error": "not found"})

    def _file(self, target: str):
        if not os.path.isfile(target):
            return self._json(404, {"error": "not found"})
        ctype = mimetypes.guess_type(target)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",):
            ctype += "; charset=utf-8"
        with open(target, "rb") as fh:
            self._send(200, fh.read(), ctype)

    # ----------------------------------------------------------------- POST
    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            body = self._body()
            if path == "/api/generate":
                return self._json(200, scenarios.generate(
                    n=int(body.get("n", 40)), m=int(body.get("m", 4)),
                    layout=body.get("layout", "uniform"), seed=body.get("seed")))
            if path == "/api/solve":
                return self._solve(body)
            return self._json(404, {"error": "not found"})
        except Exception as exc:
            traceback.print_exc()
            return self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def _solve(self, body: dict):
        sc = body.get("scenario") or {}
        methods = body.get("methods") or []
        report = scenarios.check(sc)
        if not report["ok"]:
            return self._json(400, {"error": "; ".join(report["errors"]),
                                    "check": report})
        plans, failures = {}, {}
        for key in methods:
            try:
                got = BACKEND.plan(sc, [key])
            except Exception as exc:
                traceback.print_exc()
                failures[key] = f"{type(exc).__name__}: {exc}"
                continue
            for name, plan in got.items():
                d = plan.to_json()
                d["validity"] = validity(plan, len(sc["customers"]))
                plans[name] = d
        return self._json(200, {"plans": plans, "failures": failures, "check": report})


def main():
    global BACKEND
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)
    ap.add_argument("--device", default="cpu",
                    help="cpu is plenty for one instance; use cuda if you have a GPU")
    ap.add_argument("--mock", action="store_true",
                    help="skip the models entirely and serve only the heuristic")
    opts = ap.parse_args()

    # flush everything: this is usually started with stdout redirected to a log
    print("starting -- importing the model stack takes a few seconds", flush=True)
    BACKEND = CompositeBackend(opts.runs_root, opts.device, force_mock=opts.mock)
    if BACKEND.torch:
        names = ", ".join(BACKEND.torch.available())
        print(f"models loaded from {resolve_runs_root(opts.runs_root)}", flush=True)
        print(f"  available: {names}", flush=True)
    else:
        print(f"running WITHOUT the trained models ({BACKEND.reason})", flush=True)
        print("  only the nearest-neighbour baseline will be offered", flush=True)

    srv = ThreadingHTTPServer((opts.host, opts.port), Handler)
    print(f"\n  open  http://{opts.host}:{opts.port}\n  ctrl-c to stop\n", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
