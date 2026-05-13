from src.database import get_food_data, get_nutrients_data, get_user_dri, get_user_preferences, get_food_ids_for_user
from src.chromosome import decode


def get_sample_menus(res, problem, n_samples=3):
    food_data = problem.food_data
    nutrients_data = problem.nutrients_data
    dri = problem.dri
    user_preferences = problem.user_preferences
    food_ids = problem.food_ids

    samples = []
    indices = range(min(n_samples, len(res.X)))

    for i in indices:
        x = res.X[i]
        food_ids_permuted = [food_ids[int(j) % len(food_ids)] for j in x]
        breakfast = food_ids_permuted[:94]
        lunch_dinner = food_ids_permuted[94:]

        sel_b, sel_l, nutrients_total = decode(
            breakfast, lunch_dinner, nutrients_data, dri
        )

        all_selected = sel_b + sel_l
        groups = set(food_data[fid]['foodGroupId'] for fid in all_selected)

        sample = {
            'solution_id': i + 1,
            'preference': -res.F[i][0],
            'cost': res.F[i][1],
            'time': res.F[i][2],
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