import contextlib
import csv
import os

import matplotlib
matplotlib.use('Agg')  # headless-safe: figures are saved to results/, not shown
import matplotlib.pyplot as plt
import numpy as np
from pymoo.indicators.hv import HV
from src.algorithms.nsga2 import run_nsga2
from src.algorithms.spea2 import run_spea2
from src.menu_table import get_sample_menus, print_menu_table
from src.database import get_user_dri


def calc_hypervolume(F, ref_point):
    ind = HV(ref_point=ref_point)
    return ind(F)


def plot_pareto(res_nsga2, res_spea2, user_id):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].scatter(-res_nsga2.F[:, 0], res_nsga2.F[:, 1], c='blue', label='NSGA-II')
    axes[0].scatter(-res_spea2.F[:, 0], res_spea2.F[:, 1], c='red', label='SPEA2')
    axes[0].set_xlabel('Preference')
    axes[0].set_ylabel('Cost')
    axes[0].set_title(f'Pareto Front - User {user_id}')
    axes[0].legend()

    axes[1].scatter(-res_nsga2.F[:, 0], res_nsga2.F[:, 2], c='blue', label='NSGA-II')
    axes[1].scatter(-res_spea2.F[:, 0], res_spea2.F[:, 2], c='red', label='SPEA2')
    axes[1].set_xlabel('Preference')
    axes[1].set_ylabel('Time')
    axes[1].set_title(f'Pareto Front - User {user_id}')
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(f'results/pareto_user{user_id}.png')
    plt.close()


def plot_hypervolume(hv_nsga2, hv_spea2, user_id):
    plt.figure(figsize=(10, 5))
    plt.plot(hv_nsga2, c='blue', label='NSGA-II')
    plt.plot(hv_spea2, c='red', label='SPEA2')
    plt.xlabel('Generation')
    plt.ylabel('Hypervolume')
    plt.title(f'Hypervolume Convergence - User {user_id}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'results/hypervolume_user{user_id}.png')
    plt.close()


def plot_diversity_comparison(res_with, res_without, user_id):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].scatter(-res_with.F[:, 0], res_with.F[:, 1], c='green', label='With Diversity')
    axes[0].scatter(-res_without.F[:, 0], res_without.F[:, 1], c='orange', label='Without Diversity')
    axes[0].set_xlabel('Preference')
    axes[0].set_ylabel('Cost')
    axes[0].set_title(f'Diversity Impact - User {user_id}')
    axes[0].legend()

    axes[1].scatter(-res_with.F[:, 0], res_with.F[:, 2], c='green', label='With Diversity')
    axes[1].scatter(-res_without.F[:, 0], res_without.F[:, 2], c='orange', label='Without Diversity')
    axes[1].set_xlabel('Preference')
    axes[1].set_ylabel('Time')
    axes[1].set_title(f'Diversity Impact - User {user_id}')
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(f'results/diversity_user{user_id}.png')
    plt.close()


def save_results_csv(res, algorithm_name, user_id):
    filename = f'results/{algorithm_name}_user{user_id}.csv'
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['preference', 'cost', 'time'])
        for row in res.F:
            writer.writerow([-row[0], row[1], row[2]])


def log(line):
    """Print a summary line and append it to results/summary.txt."""
    print(line)
    with open('results/summary.txt', 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def dri_compliant_menus(res, dri):
    """Decoded Pareto menus that are inside every strict [RLL, RUL] bound, and the total menu count."""
    menus = get_sample_menus(res, res.problem, n_samples=len(res.X))
    ok = [m for m in menus if all(dri[n]['RLL'] <= m['nutrients'].get(n, 0) <= dri[n]['RUL'] for n in dri)]
    return ok, len(menus)


def run_experiment(user_id, pop_size=100, n_gen=50):
    print(f"\n=== Experiment 1 & 2 - User {user_id} ===")

    print("Running NSGA-II...")
    res_nsga2, hv_nsga2 = run_nsga2(user_id=user_id, pop_size=pop_size, n_gen=n_gen, track_hv=True)

    print("Running SPEA2...")
    res_spea2, hv_spea2 = run_spea2(user_id=user_id, pop_size=pop_size, n_gen=n_gen, track_hv=True)

    plot_pareto(res_nsga2, res_spea2, user_id)
    plot_hypervolume(hv_nsga2, hv_spea2, user_id)

    save_results_csv(res_nsga2, 'nsga2', user_id)
    save_results_csv(res_spea2, 'spea2', user_id)

    dri = get_user_dri(user_id)
    log(f"[User {user_id}] NSGA-II Pareto solutions: {len(res_nsga2.F)}")
    log(f"[User {user_id}] SPEA2  Pareto solutions: {len(res_spea2.F)}")
    log(f"[User {user_id}] Final hypervolume (ref [0, 1000, 1000]): NSGA-II {hv_nsga2[-1]:.1f} | SPEA2 {hv_spea2[-1]:.1f}")
    for name, res in (('NSGA-II', res_nsga2), ('SPEA2', res_spea2)):
        ok, total = dri_compliant_menus(res, dri)
        log(f"[User {user_id}] {name} solutions inside all strict DRI bounds: {len(ok)}/{total}")
        if name == 'NSGA-II' and ok:
            best = max(ok, key=lambda m: m['preference'])
            with open(f'results/example_menu_user{user_id}.txt', 'w', encoding='utf-8') as f, contextlib.redirect_stdout(f):
                print_menu_table([best], dri)

    print(f"\n=== Sample Menus - User {user_id} ===")
    samples = get_sample_menus(res_nsga2, res_nsga2.problem, n_samples=3)
    print_menu_table(samples, dri)
    with open(f'results/sample_menus_user{user_id}.txt', 'w', encoding='utf-8') as f, contextlib.redirect_stdout(f):
        print_menu_table(samples, dri)

    return res_nsga2, res_spea2


def run_diversity_experiment(user_id, pop_size=100, n_gen=50):
    print(f"\n=== Experiment 3 - Diversity Impact - User {user_id} ===")

    print("Running NSGA-II with diversity...")
    res_with, _ = run_nsga2(user_id=user_id, pop_size=pop_size, n_gen=n_gen, track_hv=True, alpha=1.0)

    print("Running NSGA-II without diversity...")
    res_without, _ = run_nsga2(user_id=user_id, pop_size=pop_size, n_gen=n_gen, track_hv=True, alpha=0.0)

    plot_diversity_comparison(res_with, res_without, user_id)

    save_results_csv(res_with, 'nsga2_with_diversity', user_id)
    save_results_csv(res_without, 'nsga2_without_diversity', user_id)

    log(f"[User {user_id}] Diversity experiment, NSGA-II with diversity (alpha=1.0): {len(res_with.F)} solutions")
    log(f"[User {user_id}] Diversity experiment, NSGA-II without diversity (alpha=0.0): {len(res_without.F)} solutions")


if __name__ == "__main__":
    os.makedirs('results', exist_ok=True)
    open('results/summary.txt', 'w').close()
    run_experiment(user_id=1, pop_size=100, n_gen=50)
    run_experiment(user_id=2, pop_size=100, n_gen=50)
    run_diversity_experiment(user_id=1, pop_size=100, n_gen=50)