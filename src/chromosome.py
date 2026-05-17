import random

HUGE_PENALTY = 1e6

def initialize(breakfast_ids, lunch_dinner_ids):
    breakfast = breakfast_ids.copy()
    lunch_dinner = lunch_dinner_ids.copy()
    random.shuffle(breakfast)
    random.shuffle(lunch_dinner)
    return breakfast, lunch_dinner


def decode(breakfast, lunch_dinner, nutrients_data, dri, food_data=None):
    RLL = {n: dri[n]['RLL'] * 0.90 for n in dri}
    RUL = {n: dri[n]['RUL'] * 1.15 for n in dri}
    RLL_b = {n: dri[n]['RLL'] * 0.35 for n in dri}
    RUL_b = {n: dri[n]['RUL'] * 0.35 for n in dri}

    selected_breakfast = []
    nutrients_total = {n: 0 for n in dri}

    for food_id in breakfast:
        if food_data and food_data[food_id].get('preference', 0) == -1:
            continue

        food_nutrients = nutrients_data.get(food_id, {})
        energy = food_nutrients.get('Energy', 0)
        protein = food_nutrients.get('Protein', 0)

        if (nutrients_total.get('Energy', 0) + energy > RUL_b.get('Energy', 9999) or
                nutrients_total.get('Protein', 0) + protein > RUL_b.get('Protein', 9999)):
            continue

        selected_breakfast.append(food_id)
        for n in food_nutrients:
            if n in nutrients_total:
                nutrients_total[n] += food_nutrients[n]

        if (nutrients_total.get('Energy', 0) >= RLL_b.get('Energy', 0) and
                nutrients_total.get('Protein', 0) >= RLL_b.get('Protein', 0)):
            break

    selected_lunch = []

    for food_id in lunch_dinner:
        if food_data and food_data[food_id].get('preference', 0) == -1:
            continue

        food_nutrients = nutrients_data.get(food_id, {})
        skip = False
        for n in dri:
            if nutrients_total.get(n, 0) + food_nutrients.get(n, 0) > RUL.get(n, 9999):
                skip = True
                break

        if skip:
            continue

        selected_lunch.append(food_id)
        for n in food_nutrients:
            if n in nutrients_total:
                nutrients_total[n] += food_nutrients[n]

        if all(nutrients_total.get(n, 0) >= RLL.get(n, 0) for n in dri):
            break

    return selected_breakfast, selected_lunch, nutrients_total


def check_diversity(selected_breakfast, selected_lunch, food_data, min_groups=4):
    all_selected = selected_breakfast + selected_lunch
    groups = set(food_data[fid]['foodGroupId'] for fid in all_selected)
    return len(groups) >= min_groups


def calculate_objectives(selected_breakfast, selected_lunch, food_data, user_preferences):
    all_selected = selected_breakfast + selected_lunch
    preference = sum(user_preferences.get(fid, food_data[fid]['preference']) for fid in all_selected)
    cost = sum(food_data[fid]['cost'] for fid in all_selected)
    time = sum(food_data[fid]['preparingTime'] + (food_data[fid]['cookingTime'] or 0) for fid in all_selected)
    return preference, cost, time