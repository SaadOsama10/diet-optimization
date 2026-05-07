from src.penalty import apply_penalty

def evaluate(selected_breakfast, selected_lunch, nutrients_total, food_data, user_preferences, dri, lambda_=1.0):
    all_selected = selected_breakfast + selected_lunch

    preference = sum(user_preferences.get(fid, food_data[fid]['preference']) for fid in all_selected)
    cost = sum(food_data[fid]['cost'] for fid in all_selected)
    time = sum(food_data[fid]['preparingTime'] + (food_data[fid]['cookingTime'] or 0) for fid in all_selected)

    preference_penalized = apply_penalty(preference, nutrients_total, dri, lambda_)
    cost_penalized = apply_penalty(-cost, nutrients_total, dri, lambda_)
    time_penalized = apply_penalty(-time, nutrients_total, dri, lambda_)

    return preference_penalized, cost_penalized, time_penalized