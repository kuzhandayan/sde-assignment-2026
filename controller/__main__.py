"""CLI.

  python -m controller run   --url http://127.0.0.1:8700 --db state/controller.db
  python -m controller why   --db state/controller.db --workflow nw_renewal --at "D3 14:00"
  python -m controller heard --db state/controller.db --person nw_renewal:p0001234 [--day 3]
  python -m controller view  --db state/controller.db [--port 8800]      # supervisor view (HTML + JSON)
  python -m controller report --db state/controller.db --out reports/supervisor_public_01.md
"""
import argparse
import os
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(prog="controller")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--url", default="http://127.0.0.1:8700")
    r.add_argument("--db", default="state/controller.db")
    r.add_argument("-v", "--verbose", action="store_true")
    w = sub.add_parser("why", help="why did workflow X change at time T, who approved it, what happened next")
    w.add_argument("--db", default="state/controller.db")
    w.add_argument("--workflow", required=True)
    w.add_argument("--at", required=True, help="'D3 14:00' or ISO timestamp")
    w.add_argument("--json", action="store_true")
    h = sub.add_parser("heard", help="what a customer heard on each call, and why that variant was live")
    h.add_argument("--db", default="state/controller.db")
    h.add_argument("--person", required=True)
    h.add_argument("--day", type=int)
    v = sub.add_parser("view")
    v.add_argument("--db", default="state/controller.db")
    v.add_argument("--host", default="127.0.0.1")
    v.add_argument("--port", type=int, default=8800)
    rp = sub.add_parser("report")
    rp.add_argument("--db", default="state/controller.db")
    rp.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        # Reproducible runs: string hashing (set/dict iteration order) must not vary between processes,
        # otherwise tiny rounding differences in allocations change later decisions.
        if os.environ.get("PYTHONHASHSEED") != "0":
            os.environ["PYTHONHASHSEED"] = "0"
            os.execv(sys.executable, [sys.executable, "-m", "controller", *(argv or sys.argv[1:])])
        from .loop import main_run
        main_run(a.url, a.db, a.verbose)
    elif a.cmd == "why":
        from .audit import why
        print(why(a.db, a.workflow, a.at, as_json=a.json))
    elif a.cmd == "heard":
        from .audit import heard
        print(heard(a.db, a.person, a.day))
    elif a.cmd == "view":
        from .view import serve
        serve(a.db, a.host, a.port)
    elif a.cmd == "report":
        from .view import markdown_report
        out = markdown_report(a.db)
        if a.out:
            open(a.out, "w").write(out)
        print(out)


if __name__ == "__main__":
    main()
