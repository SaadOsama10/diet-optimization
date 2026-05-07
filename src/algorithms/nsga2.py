import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize

from src.database import get_food_data, get_nutrients_data, get_user_dri, get_user_preferences
from src.chromosome import decode
from src.objectives import evaluate


class DietProblem(Problem):
    def __init__(self, user_id):
        self.food_data = get_food_data()
        self.nutrients_data = get_nutrients_data()
        self.dri = get_user_dri(user_id)
        self.user_preferences = get_user_preferences(user_id)
        self.food_ids = list(self.food_data.keys())

        super().__init__(
            n_var=405,
            n_obj=3,
            xl=0,
            xu=404,
            vtype=int
        )

    def _evaluate(self, X, out, *args, **kwargs):
        F = []
        for x in X:
            food_ids_permuted = [self.food_ids[int(i)] for i in x]
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


def run_nsga2(user_id, pop_size=100, n_gen=200):
    problem = DietProblem(user_id)

    algorithm = NSGA2(
        pop_size=pop_size,
    )

    res = minimize(
        problem,
        algorithm,
        termination=('n_gen', n_gen),
        verbose=True
    )

    return res


if __name__ == "__main__":
    res = run_nsga2(user_id=1, pop_size=50, n_gen=10)
    print("Done!")
    print(f"Pareto solutions: {len(res.F)}")