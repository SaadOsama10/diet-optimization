"""Thin driver for the live demo and the parity check.

It calls the repository's own run_nsga2 / run_spea2 / get_sample_menus unchanged. The only
addition is seeding: the original code calls pymoo's minimize() without a seed (so every run
differs). To make runs reproducible without editing src/, the seed is injected by wrapping the
`minimize` name that src/algorithms/*.py imported; nothing else about the call changes.

The same file runs under CPython (parity reference) and inside Pyodide (the browser demo).
"""
import json

import src.algorithms.nsga2 as _nsga2
import src.algorithms.spea2 as _spea2
from src.algorithms.nsga2 import run_nsga2
from src.algorithms.spea2 import run_spea2
from src.database import get_user_dri
from src.menu_table import get_sample_menus

ALGORITHMS = {"nsga2": run_nsga2, "spea2": run_spea2}


def _seed_minimize(module, seed):
    original = getattr(module, "_unseeded_minimize", module.minimize)
    module._unseeded_minimize = original
    module.minimize = lambda *args, **kwargs: original(*args, seed=seed, **kwargs)


def run(user_id, algorithm, seed, pop_size=100, n_gen=50):
    user_id, seed, pop_size, n_gen = int(user_id), int(seed), int(pop_size), int(n_gen)
    _seed_minimize(_nsga2, seed)
    _seed_minimize(_spea2, seed)
    res, hv_history = ALGORITHMS[algorithm](user_id=user_id, pop_size=pop_size, n_gen=n_gen, track_hv=True)

    dri = get_user_dri(user_id)
    menus = get_sample_menus(res, res.problem, n_samples=len(res.X))
    solutions = []
    for menu, f in zip(menus, res.F):
        compliant = all(dri[n]["RLL"] <= menu["nutrients"].get(n, 0) <= dri[n]["RUL"] for n in dri)
        solutions.append({
            "F": [float(v) for v in f],  # pymoo objectives, penalty included
            "preference": float(menu["preference"]),
            "cost": float(menu["cost"]),
            "time": float(menu["time"]),
            "n_groups": int(menu["n_groups"]),
            "nutrients": {n: float(v) for n, v in menu["nutrients"].items()},
            "breakfast": menu["breakfast"],
            "lunch_dinner": menu["lunch_dinner"],
            "compliant": compliant,
        })
    compliant_idx = [i for i, s in enumerate(solutions) if s["compliant"]]
    best = max(compliant_idx, key=lambda i: solutions[i]["preference"]) if compliant_idx else None

    return json.dumps({
        "user_id": user_id, "algorithm": algorithm, "seed": seed, "pop_size": pop_size, "n_gen": n_gen,
        "hypervolume": float(hv_history[-1]),
        "hv_history": [float(v) for v in hv_history],
        "n_solutions": len(solutions),
        "n_compliant": len(compliant_idx),
        "best_index": best,
        "dri": dri,
        "solutions": solutions,
    })
