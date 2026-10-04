from src.database import get_user_dri
from src.chromosome import decode, calculate_objectives


def get_sample_menus(res, problem, n_samples=3):
    food_data = problem.food_data
    nutrients_data = problem.nutrients_data
    dri = problem.dri
    user_preferences = problem.user_preferences
    breakfast_ids = problem.breakfast_ids
    lunch_dinner_ids = problem.lunch_dinner_ids

    samples = []
    indices = range(min(n_samples, len(res.X)))

    for i in indices:
        x = res.X[i]
        n_b = len(breakfast_ids)
        breakfast_perm = [breakfast_ids[int(j) % n_b] for j in x[:n_b]]
        lunch_perm = [lunch_dinner_ids[int(j) % len(lunch_dinner_ids)] for j in x[n_b:]]

        sel_b, sel_l, nutrients_total = decode(
            breakfast_perm, lunch_perm, nutrients_data, dri, food_data
        )

        all_selected = sel_b + sel_l
        groups = set(food_data[fid]['foodGroupId'] for fid in all_selected)

        # raw objective values of the decoded menu (res.F also contains the penalty term)
        preference, cost, time = calculate_objectives(sel_b, sel_l, food_data, user_preferences)

        sample = {
            'solution_id': i + 1,
            'preference': preference,
            'cost': cost,
            'time': time,
            'nutrients': nutrients_total,
            'n_groups': len(groups),
            'breakfast': [food_data[fid]['name'] for fid in sel_b],
            'lunch_dinner': [food_data[fid]['name'] for fid in sel_l],
        }
        samples.append(sample)

    return samples


def print_menu_table(samples, dri):
    for s in samples:
        print(f"\n{'='*60}")
        print(f"Solution {s['solution_id']}")
        print(f"{'='*60}")
        print(f"Preference: {s['preference']:.2f} | Cost: {s['cost']:.2f} | Time: {s['time']:.0f} min")
        print(f"Food Groups: {s['n_groups']}")

        print(f"\nBreakfast:")
        for food in s['breakfast']:
            print(f"  - {food}")

        print(f"\nLunch/Dinner:")
        for food in s['lunch_dinner']:
            print(f"  - {food}")

        print(f"\nNutrient Totals vs DRI:")
        print(f"{'Nutrient':<25} {'Total':>10} {'RLL':>10} {'RUL':>10} {'Status':>10}")
        print("-" * 65)
        for n in dri:
            total = s['nutrients'].get(n, 0)
            rll = dri[n]['RLL']
            rul = dri[n]['RUL']
            status = '✅' if rll <= total <= rul else '❌'
            print(f"{n:<25} {total:>10.1f} {rll:>10.1f} {rul:>10.1f} {status:>10}")