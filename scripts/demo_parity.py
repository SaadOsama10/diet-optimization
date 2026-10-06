"""Parity check: the browser demo (pymoo in Pyodide) must reproduce the desktop Python run.

    python scripts/demo_parity.py reference            # run the original code under CPython -> docs/demo/parity/reference.json
    python scripts/demo_parity.py compare browser.json # compare a file written by scripts/demo_parity_browser.mjs

Each case is user x algorithm x seed at the project's settings (population 100, 50 generations). A case
passes when the Pareto front objectives (all 100 x 3 values), the decoded menus, the hypervolume, the
number of fully DRI-compliant solutions and the best compliant menu all agree.
"""
import contextlib
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "docs" / "demo")]

CASES = [(u, a, s) for u in (1, 2) for a in ("nsga2", "spea2") for s in (42, 2024)]
PARITY_DIR = ROOT / "docs" / "demo" / "parity"
HV_RTOL = 1e-12   # moocore (C) vs the pure-Python hypervolume differ by at most a few ulps
F_ATOL = 1e-9


def summarise(run_json):
    r = json.loads(run_json) if isinstance(run_json, str) else run_json
    sols = r["solutions"]
    menus = [[s["breakfast"], s["lunch_dinner"], float(s["preference"]), float(s["cost"]), float(s["time"]), int(s["n_groups"])] for s in sols]  # float(): JS turns 170.0 into 170
    best = sols[r["best_index"]] if r["best_index"] is not None else None
    return {
        "hypervolume": r["hypervolume"],
        "n_solutions": r["n_solutions"],
        "n_compliant": r["n_compliant"],
        "best_index": r["best_index"],
        "best_menu": best and {"preference": float(best["preference"]), "cost": float(best["cost"]), "time": float(best["time"]),
                               "n_groups": int(best["n_groups"]), "breakfast": best["breakfast"], "lunch_dinner": best["lunch_dinner"]},
        "F": [s["F"] for s in sols],
        "compliant": [s["compliant"] for s in sols],
        "menus_sha256": hashlib.sha256(json.dumps(menus, sort_keys=True).encode()).hexdigest(),
    }


def key(u, a, s):
    return f"user{u}_{a}_seed{s}"


def make_reference():
    import runner
    out = {}
    for u, a, s in CASES:
        with contextlib.redirect_stdout(io.StringIO()):
            res = runner.run(u, a, s, 100, 50)
        out[key(u, a, s)] = summarise(res)
        print(key(u, a, s), "HV", out[key(u, a, s)]["hypervolume"], "compliant", out[key(u, a, s)]["n_compliant"])
    PARITY_DIR.mkdir(exist_ok=True)
    (PARITY_DIR / "reference.json").write_text(json.dumps(out, indent=1))


def compare(browser_file):
    ref = json.loads((PARITY_DIR / "reference.json").read_text())
    got = json.loads(Path(browser_file).read_text())
    rows, ok_all = [], True
    for u, a, s in CASES:
        k = key(u, a, s)
        r, b = ref[k], summarise(got[k])
        f_diff = max(abs(x - y) for rf, bf in zip(r["F"], b["F"]) for x, y in zip(rf, bf))
        hv_rel = abs(r["hypervolume"] - b["hypervolume"]) / r["hypervolume"]
        checks = {
            "front": f_diff <= F_ATOL and len(r["F"]) == len(b["F"]),
            "hv": hv_rel <= HV_RTOL,
            "compliant": r["n_compliant"] == b["n_compliant"] and r["compliant"] == b["compliant"],
            "best menu": r["best_index"] == b["best_index"] and r["best_menu"] == b["best_menu"],
            "menus": r["menus_sha256"] == b["menus_sha256"],
        }
        ok = all(checks.values())
        ok_all &= ok
        rows.append((k, ok, f_diff, hv_rel, r["hypervolume"], r["n_compliant"], [n for n, v in checks.items() if not v]))
    print(f"{'case':26} {'result':6} {'max |dF|':>10} {'HV rel diff':>12} {'HV':>16} compliant")
    for k, ok, fd, hr, hv, nc, failed in rows:
        print(f"{k:26} {'PASS' if ok else 'FAIL':6} {fd:10.1e} {hr:12.1e} {hv:16.1f} {nc:>5} {','.join(failed)}")
    print("\nPARITY:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["reference"]:
        make_reference()
    elif sys.argv[1:2] == ["compare"] and len(sys.argv) == 3:
        sys.exit(compare(sys.argv[2]))
    else:
        sys.exit(__doc__)
