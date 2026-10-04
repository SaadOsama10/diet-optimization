import numpy as np
from pymoo.algorithms.moo.spea2 import SPEA2
from pymoo.core.problem import Problem
from pymoo.core.callback import Callback
from pymoo.indicators.hv import HV
from pymoo.optimize import minimize

from src.database import get_food_data, get_nutrients_data, get_user_dri, get_user_preferences, get_breakfast_food_ids, get_lunch_dinner_food_ids
from src.chromosome import decode
from src.objectives import evaluate


class HVCallback(Callback):
    def __init__(self, ref_point):
        super().__init__()
        self.ref_point = ref_point
        self.hv_history = []

    def notify(self, algorithm):
        F = algorithm.opt.get("F")
        if F is not None and len(F) > 0:
            ind = HV(ref_point=self.ref_point)
            self.hv_history.append(ind(F))
        else:
            self.hv_history.append(0)


class DietProblem(Problem):
    def __init__(self, user_id, alpha=1.0):
        self.food_data = get_food_data()
        self.nutrients_data = get_nutrients_data()
        self.dri = get_user_dri(user_id)
        self.user_preferences = get_user_preferences(user_id)
        self.breakfast_ids = get_breakfast_food_ids(user_id)
        self.lunch_dinner_ids = get_lunch_dinner_food_ids(user_id)
        self.alpha = alpha

        n_var = len(self.breakfast_ids) + len(self.lunch_dinner_ids)

        super().__init__(
            n_var=n_var,
            n_obj=3,
            xl=0,
            xu=n_var - 1,
            vtype=int
        )

    def _evaluate(self, X, out, *args, **kwargs):
        F = []
        for x in X:
            n_b = len(self.breakfast_ids)
            breakfast_perm = [self.breakfast_ids[int(i) % n_b] for i in x[:n_b]]
            lunch_perm = [self.lunch_dinner_ids[int(i) % len(self.lunch_dinner_ids)] for i in x[n_b:]]

            sel_b, sel_l, nutrients_total = decode(
                breakfast_perm, lunch_perm, self.nutrients_data, self.dri, self.food_data
            )

            pref, cost, time = evaluate(
                sel_b, sel_l, nutrients_total,
                self.food_data, self.user_preferences, self.dri,
                alpha=self.alpha
            )

            # pymoo minimizes. evaluate() returns every objective in maximize form
            # (pref - R, -cost - R, -time - R), so all three are negated here.
            F.append([-pref, -cost, -time])

        out["F"] = np.array(F)


def run_spea2(user_id, pop_size=100, n_gen=200, track_hv=False, alpha=1.0):
    problem = DietProblem(user_id, alpha=alpha)
    ref_point = np.array([0.0, 1000.0, 1000.0])
    callback = HVCallback(ref_point) if track_hv else None

    algorithm = SPEA2(pop_size=pop_size)

    res = minimize(
        problem,
        algorithm,
        termination=('n_gen', n_gen),
        verbose=True,
        **({"callback": callback} if callback is not None else {})
    )

    if track_hv:
        return res, callback.hv_history
    return res


if __name__ == "__main__":
    res = run_spea2(user_id=1, pop_size=50, n_gen=10)
    print("Done!")
    print(f"Pareto solutions: {len(res.F)}")