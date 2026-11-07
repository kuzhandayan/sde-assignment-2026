"""Crash-recovery test (C13)."""
import argparse
import json
import os
import random
import signal
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="scenarios/public_02_incidents.yaml")
    ap.add_argument("--kills", type=int, default=4, help="random SIGKILLs on top of the injected crash points")
    ap.add_argument("--port", type=int, default=8760)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="runs/crash_recovery.md")
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    run_dir, db = ROOT / "runs" / "crash_test", ROOT / "state" / "crash_test.db"
    marker = ROOT / "state" / ".crash_fired_test"
    for p in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm"), marker):
        p.unlink(missing_ok=True)
    sim = subprocess.Popen([sys.executable, "-m", "sim", "serve", "--scenario", a.scenario, "--run-dir",
                            str(run_dir), "--force", "--port", str(a.port)], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log = []

    class _Log(list):
        def append(self, x):
            print(f"[{time.strftime('%H:%M:%S')}] {x}", flush=True)
            super().append(x)
    log = _Log()
    print(f"[{time.strftime('%H:%M:%S')}] crash test: simulator starting on port {a.port}; each line below is one "
          f"controller start (kills are deliberate)", flush=True)
    url = f"http://127.0.0.1:{a.port}"
    env = {**os.environ, "CRASH_POINTS": "after_approval_post,after_apply_post,after_auto_put,mid_chunk",
           "CRASH_MARKER": str(marker)}
    starts = 0
    try:
        kills_left = a.kills
        while True:
            starts += 1
            t0 = time.time()
            p = subprocess.Popen([sys.executable, "-m", "controller", "run", "--url", url, "--db", str(db)],
                                 cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            kill_after = rnd.uniform(4, 20) if kills_left > 0 else None
            try:
                out, _ = p.communicate(timeout=kill_after)
            except subprocess.TimeoutExpired:
                p.send_signal(signal.SIGKILL)
                out, _ = p.communicate()
                kills_left -= 1
                st = __import__("httpx").get(f"{url}/sim/state", timeout=30).json()
                log.append(f"start {starts}: SIGKILL after {time.time() - t0:.1f}s wall, sim at {st['ts']}")
                continue
            inj = [l for l in out.splitlines() if "fault-injection" in l]
            if p.returncode == 137 and inj:
                st = __import__("httpx").get(f"{url}/sim/state", timeout=30).json()
                log.append(f"start {starts}: {inj[-1].strip()} (sim at {st['ts']})")
                continue
            log.append(f"start {starts}: exited {p.returncode} after {time.time() - t0:.1f}s")
            if p.returncode != 0:
                print(out[-3000:])
            break
        print(f"[{time.strftime('%H:%M:%S')}] verifying exactly-once, approvals and aggregates...", flush=True)
        checks = verify(url, run_dir, db)
    finally:
        sim.terminate()
        sim.wait()
    ok = all(c[1] for c in checks)
    md = ["# Crash-recovery test", "", f"Scenario `{a.scenario}`, {starts} controller starts on one SQLite file.",
          "Injected hard exits (like kill -9) right after each kind of POST/PUT is sent but before its result is "
          "recorded, and in the middle of an ingest transaction; plus random SIGKILLs.", "", "## Timeline", ""]
    md += [f"- {l}" for l in log]
    md += ["", "## Checks", ""] + [f"- {'PASS' if c[1] else 'FAIL'} — {c[0]}: {c[2]}" for c in checks]
    md += ["", f"**Result: {'PASS' if ok else 'FAIL'}**",
           "", "Grade of the crashed run (same metrics as a normal run):", "", "```",
           subprocess.run([sys.executable, "-m", "sim", "grade", "--run", str(run_dir), "--baseline",
                           str(ROOT / "runs" / "base_public_02")], cwd=ROOT, capture_output=True, text=True
                          ).stdout.split("## Changes")[0].strip() if (ROOT / "runs" / "base_public_02").exists()
           else "(baseline not generated)", "```"]
    Path(ROOT / a.out).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / a.out).write_text("\n".join(md))
    print("\n".join(md))
    sys.exit(0 if ok else 1)


def verify(url, run_dir, db_path):
    import httpx
    c = httpx.Client(base_url=url, timeout=60)
    st = c.get("/sim/state").json()
    db = sqlite3.connect(db_path)
    out = [("scenario finished", st["finished"], st["ts"])]
    wfs = [w["workflow_id"] for w in c.get("/workflows").json()]
    remote = [x for w in wfs for x in c.get("/approvals", params={"workflow_id": w}).json()]
    ours = {r[0]: r for r in db.execute("SELECT proposal_id, status, approval_id FROM proposals WHERE channel='approval'")}
    missing = [x["proposal_id"] for x in remote if x["proposal_id"] not in ours]
    out.append(("every simulator approval is in our store", not missing, f"{len(remote)} approvals, missing {missing}"))
    mism = [(x["proposal_id"], x["status"], ours[x["proposal_id"]][1]) for x in remote if x["proposal_id"] in ours
            and not (x["status"] == ours[x["proposal_id"]][1] or (x["status"] == "approved" and
                                                                  ours[x["proposal_id"]][1] in ("stale", "lapsed")))]
    out.append(("our proposal states agree with the simulator", not mism, f"mismatches {mism}"))
    sim_log = [json.loads(l) for l in (run_dir / "sim_log.jsonl").read_text().splitlines()]
    applied = Counter(r["approval_id"] for r in sim_log if r["kind"] == "approval_applied")
    dup = [k for k, v in applied.items() if v > 1]
    out.append(("no approval applied twice", not dup, f"{sum(applied.values())} applied, duplicates {dup}"))
    kinds = Counter(r["kind"] for r in sim_log)
    out.append(("no apply conflicts / lapses", kinds["apply_conflict"] == 0 and kinds["approval_lapsed"] == 0,
                f"apply_conflict={kinds['apply_conflict']}, lapsed={kinds['approval_lapsed']}"))
    lost = []
    for w in wfs:
        for v in c.get(f"/workflows/{w}/config/history").json():
            if v["actor"].startswith("controller"):
                r = db.execute("SELECT status FROM proposals WHERE proposal_id=?", (v["proposal_id"],)).fetchone()
                if not r or r[0] != "applied":
                    lost.append((w, v["version"], v["proposal_id"], r))
    out.append(("every applied controller change is 'applied' in our store", not lost, f"lost {lost}"))
    ours_ev = db.execute("SELECT SUM(events) FROM chunks_done").fetchone()[0]
    out.append(("ingestion exactly-once (event count)", ours_ev == st["last_event_id"],
                f"ours {ours_ev} vs simulator {st['last_event_id']}"))
    conn = Counter()
    for f in sorted((run_dir / "history").glob("*.jsonl")) + sorted((run_dir / "events").glob("*.jsonl")):
        for l in f.open():
            if '"type":"call"' in l and '"connected":true' in l:
                conn[json.loads(l)["workflow_id"]] += 1
    agg = dict(db.execute("SELECT workflow_id, SUM(conn) FROM agg_eng GROUP BY workflow_id").fetchall())
    out.append(("connected-call aggregates match a recount of raw chunks", dict(conn) == agg,
                f"recount {dict(conn)} vs store {agg}"))
    return out


if __name__ == "__main__":
    main()
