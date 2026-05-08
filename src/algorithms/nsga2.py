import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.core.callback import Callback
from pymoo.indicators.hv import HV
from pymoo.optimize import minimize

from src.database import get_food_data, get_nutrients_data, get_user_dri, get_user_preferences, get_food_ids_for_user
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
    def __init__(self, user_id):
        self.food_data = get_food_data()
        self.nutrients_data = get_nutrients_data()
        self.dri = get_user_dri(user_id)
        self.user_preferences = get_user_preferences(user_id)
        self.food_ids = get_food_ids_for_user(user_id)

        super().__init__(
            n_var=len(self.food_ids),
            n_obj=3,
            xl=0,
            xu=len(self.food_ids) - 1,
            vtype=int
        )

    def _evaluate(self, X, out, *args, **kwargs):
        F = []
        for x in X:
            food_ids_permuted = [self.food_ids[int(i) % len(self.food_ids)] for i in x]
            breakfast = food_ids_permuted[:94]
            lunch_dinner = food_ids_permuted[94:]

            sel_b, sel_l, nutrients_total = decode(
                breakfast, lunch_dinner, self.nutrients_data, self.dri
            )

            pref, cost, time = evaluate(
                sel_b, sel_l, nutrients_total,
                self.food_data, self.user_preferences, self.dri
            )

            F.append([-pref, cost, time])

        out["F"] = np.array(F)


def run_nsga2(user_id, pop_size=100, n_gen=200, track_hv=False):
    problem = DietProblem(user_id)
    ref_point = np.array([0.0, 1000.0, 1000.0])
    callback = HVCallback(ref_point) if track_hv else None

    algorithm = NSGA2(pop_size=pop_size)

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
    res = run_nsga2(user_id=1, pop_size=50, n_gen=10)
    print("Done!")
    print(f"Pareto solutions: {len(res.F)}")