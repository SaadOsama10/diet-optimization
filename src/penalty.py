def calculate_penalty(nutrients_total, dri):
    R = 0
    for n in dri:
        RLL = dri[n]['RLL']
        RUL = dri[n]['RUL']
        v = nutrients_total.get(n, 0)
        viol_low = max(0, RLL - v) / (RUL - RLL)
        viol_high = max(0, v - RUL) / (RUL - RLL)
        R += 0.7 * viol_low + 0.3 * viol_high
    return R

def calculate_diversity_penalty(selected_breakfast, selected_lunch, food_data, alpha=1.0):
    all_selected = selected_breakfast + selected_lunch
    if not all_selected:
        return alpha
    groups = set(food_data[fid]['foodGroupId'] for fid in all_selected)
    return alpha * (1 / len(groups))

def apply_penalty(objective_value, nutrients_total, dri, sel_b=None, sel_l=None, food_data=None, lambda_=1.0, alpha=1.0):
    R = calculate_penalty(nutrients_total, dri)
    if sel_b is not None and sel_l is not None and food_data is not None:
        R += calculate_diversity_penalty(sel_b, sel_l, food_data, alpha)
    return objective_value - lambda_ * R