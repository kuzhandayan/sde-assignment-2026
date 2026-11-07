"""Evaluate the controller across random seeds of the public scenarios (robustness, not tuning).

Only the scenario's `seed` is changed (a temporary copy under runs/eval/). The controller still only talks to
the simulator over HTTP. Prints one line per run and the mean per scenario.

    python scripts/eval_seeds.py --seeds 3 --scenarios public_01_dev public_02_incidents
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(scen: str, seed: int, port: int) -> dict:
    src = (ROOT / "scenarios" / f"{scen}.yaml").read_text()
    d = ROOT / "runs" / "eval"
    d.mkdir(parents=True, exist_ok=True)
    tag = f"{scen}_s{seed}"
    yml = d / f"{tag}.yaml"
    yml.write_text(re.sub(r"^seed: \d+", f"seed: {seed}", src, count=1, flags=re.M))
    base, mine, db = d / f"base_{tag}", d / f"mine_{tag}", d / f"{tag}.db"
    for p in (mine,):
        shutil.rmtree(p, ignore_errors=True)
    for ext in ("", "-wal", "-shm"):
        Path(str(db) + ext).unlink(missing_ok=True)
    if not base.exists():
        subprocess.run([sys.executable, "-m", "sim", "baseline", "--scenario", str(yml), "--run-dir", str(base)],
                       cwd=ROOT, check=True, capture_output=True)
    sim = subprocess.Popen([sys.executable, "-m", "sim", "serve", "--scenario", str(yml), "--run-dir", str(mine),
                            "--force", "--port", str(port)], cwd=ROOT, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    try:
        t0 = time.time()
        subprocess.run([sys.executable, "-m", "controller", "run", "--url", f"http://127.0.0.1:{port}", "--db",
                        str(db)], cwd=ROOT, check=True, capture_output=True)
        wall = time.time() - t0
    finally:
        sim.terminate()
        sim.wait()
    g = json.loads(subprocess.run([sys.executable, "-m", "sim", "grade", "--run", str(mine), "--baseline", str(base),
                                   "--json"], cwd=ROOT, check=True, capture_output=True, text=True).stdout)
    a = g["delta_vs_baseline"]["ALL"]
    v = g["controller_changes"]["verdicts"]
    mttr = [i.get("mttr_minutes") for i in g["incidents"] if "mttr_minutes" in i]
    per = {w: round(d["conclusion_rate"] * 100, 1) for w, d in g["delta_vs_baseline"].items() if w != "ALL"}
    return {"scenario": scen, "seed": seed, "conclusion": a["conclusion_rate"] * 100, "pickup": a["pickup_rate"] * 100,
            "engagement": a["engagement_rate"] * 100, "harmful": v.get("harmful", 0),
            "beneficial": v.get("beneficial", 0), "changes": g["controller_changes"]["count"],
            "gap": (g["kpis"]["ALL"]["engagement_gap_captured"] or 0) * 100, "mttr": mttr,
            "requests": g["governance"]["approval_requests"], "credits": g["credits_used"], "per_wf": per,
            "wall_s": round(wall, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--scenarios", nargs="+", default=["public_01_dev", "public_02_incidents"])
    ap.add_argument("--out")
    a = ap.parse_args()
    res = []
    for scen in a.scenarios:
        for i in range(a.seeds):
            r = run(scen, a.first_seed + i, 8790 + i)
            res.append(r)
            print(f"{scen} seed={r['seed']}: conclusion {r['conclusion']:+.1f}%  pickup {r['pickup']:+.1f}%  "
                  f"engagement {r['engagement']:+.1f}%  gap {r['gap']:.0f}%  harmful {r['harmful']}/{r['changes']}  "
                  f"mttr {r['mttr']}  requests {r['requests']}  per-wf {r['per_wf']}  ({r['wall_s']}s)", flush=True)
    for scen in a.scenarios:
        rs = [r for r in res if r["scenario"] == scen]
        m = lambda k: sum(r[k] for r in rs) / len(rs)
        print(f"MEAN {scen}: conclusion {m('conclusion'):+.1f}%  pickup {m('pickup'):+.1f}%  engagement "
              f"{m('engagement'):+.1f}%  gap {m('gap'):.0f}%  harmful {m('harmful'):.1f}  changes {m('changes'):.0f}")
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
