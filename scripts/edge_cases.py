"""End-to-end edge cases against a real simulator."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "runs" / "edge"
PY = sys.executable


def scenario(name, src="public_01_dev", **over):
    text = (ROOT / "scenarios" / f"{src}.yaml").read_text()
    for k, v in over.items():
        text = re.sub(rf"^{k}: .*$", f"{k}: {v}", text, count=1, flags=re.M)
    p = E / f"{name}.yaml"
    p.write_text(text)
    return p


def sim(yml, port, run):
    shutil.rmtree(run, ignore_errors=True)
    return subprocess.Popen([PY, "-m", "sim", "serve", "--scenario", str(yml), "--run-dir", str(run), "--force",
                             "--port", str(port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_up(port, t=120):
    import httpx
    end = time.time() + t
    while time.time() < end:
        try:
            if httpx.get(f"http://127.0.0.1:{port}/health", timeout=2).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("sim did not start")


def ctl(port, db, env=None, timeout=900, wait=None):
    e = {**os.environ, **(env or {})}
    if wait is not None:
        e["CONTROLLER_WAIT_S"] = str(wait)
    return subprocess.run([PY, "-m", "controller", "run", "--url", f"http://127.0.0.1:{port}", "--db", str(db)],
                          cwd=ROOT, env=e, capture_output=True, text=True, timeout=timeout)


def fresh_db(name):
    db = E / f"{name}.db"
    for ext in ("", "-wal", "-shm", ".lock"):
        Path(str(db) + ext).unlink(missing_ok=True)
    return db


def state(port):
    import httpx
    return httpx.get(f"http://127.0.0.1:{port}/sim/state", timeout=10).json()


def q(db, sql):
    import sqlite3
    return sqlite3.connect(db).execute(sql).fetchall()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/edge_cases.md")
    a = ap.parse_args()
    E.mkdir(parents=True, exist_ok=True)
    short = scenario("short", days=2, history_days=3)
    res = []

    print(f"[{time.strftime('%H:%M:%S')}] running 9 edge cases (about 2 minutes); one line per case", flush=True)

    def record(name, ok, detail):
        res.append((name, ok, detail))
        print(f"[{time.strftime('%H:%M:%S')}] {'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)

    # 1. controller first, simulator later
    db = fresh_db("c1")
    p = subprocess.Popen([PY, "-m", "controller", "run", "--url", "http://127.0.0.1:8811", "--db", str(db)], cwd=ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(6)
    s = sim(short, 8811, E / "run_c1")
    out, _ = p.communicate(timeout=900)
    st = state(8811)
    s.terminate()
    record("1 controller starts before simulator", p.returncode == 0 and st["finished"],
           f"exit {p.returncode}, sim finished={st['finished']}")

    # 2. simulator never up
    t0 = time.time()
    r = ctl(8812, fresh_db("c2"), wait=5, timeout=60)
    record("2 simulator unreachable", r.returncode != 0 and "not reachable" in (r.stdout + r.stderr),
           f"exit {r.returncode} after {time.time() - t0:.0f}s: {(r.stdout + r.stderr).strip().splitlines()[-1][:120]}")

    # 3. mid-scenario start
    s = sim(short, 8813, E / "run_c3")
    wait_up(8813)
    import httpx
    httpx.post("http://127.0.0.1:8813/sim/advance", json={"minutes": 1440 + 720}, timeout=120)
    db = fresh_db("c3")
    r = ctl(8813, db)
    st = state(8813)
    ours = q(db, "SELECT SUM(events) FROM chunks_done")[0][0]
    s.terminate()
    record("3 start mid-scenario (sim already at D1 12:00)", r.returncode == 0 and st["finished"] and
           ours == st["last_event_id"], f"exit {r.returncode}, events ours {ours} = sim {st['last_event_id']}")

    # 4. start after the scenario finished, 5. restart on the same DB after finishing
    s = sim(short, 8814, E / "run_c4")
    wait_up(8814)
    while not httpx.post("http://127.0.0.1:8814/sim/advance", json={"minutes": 1440}, timeout=120).json()["finished"]:
        pass
    db = fresh_db("c4")
    r = ctl(8814, db)
    props = q(db, "SELECT COUNT(*) FROM proposals")[0][0]
    record("4 start after scenario finished", r.returncode == 0 and props == 0,
           f"exit {r.returncode}, proposals sent {props}")
    r2 = ctl(8814, db)
    props2 = q(db, "SELECT COUNT(*) FROM proposals")[0][0]
    ev = q(db, "SELECT SUM(events) FROM chunks_done")[0][0]
    record("5 restart on finished DB", r2.returncode == 0 and props2 == props and ev == state(8814)["last_event_id"],
           f"exit {r2.returncode}, proposals {props}->{props2}, events {ev}")
    s.terminate()

    # 6. DB from another world
    other = scenario("other", seed=999, days=2, history_days=3)
    s = sim(other, 8815, E / "run_c6")
    wait_up(8815)
    r = ctl(8815, E / "c4.db", wait=30)
    s.terminate()
    record("6 DB from a different simulator run", r.returncode != 0 and "another simulator run" in r.stdout + r.stderr,
           f"exit {r.returncode}: refused")

    # 7. two controllers on one DB
    s = sim(short, 8816, E / "run_c7")
    wait_up(8816)
    db = fresh_db("c7")
    p1 = subprocess.Popen([PY, "-m", "controller", "run", "--url", "http://127.0.0.1:8816", "--db", str(db)], cwd=ROOT,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    r = ctl(8816, db, timeout=60)
    p1.wait(timeout=900)
    st = state(8816)
    s.terminate()
    record("7 second controller on the same DB", r.returncode != 0 and "already running" in r.stdout + r.stderr
           and p1.returncode == 0 and st["finished"], f"second exit {r.returncode}; first exit {p1.returncode}")

    # 8. incident with too few credits
    poor = scenario("poor", src="public_02_incidents", credits=2)
    s = sim(poor, 8817, E / "run_c8")
    db = fresh_db("c8")
    r = ctl(8817, db, wait=120)
    st = state(8817)
    s.terminate()
    alerts = [x[0] for x in q(db, "SELECT summary FROM alerts WHERE severity='page'")]
    inc = q(db, "SELECT status, json_extract(detail,'$.phase') FROM incidents")
    record("8 hallucination incident with 2 credits", r.returncode == 0 and st["finished"] and
           st["credits_remaining"] >= 0 and any("credit" in x or "no validated fix" in x for x in alerts),
           f"exit {r.returncode}, credits left {st['credits_remaining']}, incident {inc}, pages {alerts[:3]}")

    # 9. simulator restarts mid-run (new world) under a running controller
    s = sim(short, 8818, E / "run_c9")
    db = fresh_db("c9")
    p = subprocess.Popen([PY, "-m", "controller", "run", "--url", "http://127.0.0.1:8818", "--db", str(db)], cwd=ROOT,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(12)
    p.kill()
    p.wait()
    s.terminate()
    s.wait()
    s = sim(short, 8818, E / "run_c9b")   # same scenario, brand new world at D0
    wait_up(8818)
    r = ctl(8818, db, wait=30, timeout=120)
    s.terminate()
    record("9 simulator restarted under the controller", r.returncode != 0 and "another simulator run" in
           r.stdout + r.stderr, f"exit {r.returncode}: refused to mix the old DB with the new world")

    ok = all(x[1] for x in res)
    md = ["# Edge-case end-to-end tests", "", "`python scripts/edge_cases.py` — every case starts from a fresh "
          "simulator run dir and a fresh controller DB, against the real simulator over HTTP.", "",
          "| case | result | detail |", "|---|---|---|"]
    md += [f"| {n} | {'PASS' if o else 'FAIL'} | {d.replace('|', '/')} |" for n, o, d in res]
    md += ["", f"**{sum(x[1] for x in res)}/{len(res)} passed.**"]
    (ROOT / a.out).write_text("\n".join(md) + "\n")
    print("\n".join(md))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
