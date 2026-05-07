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

def apply_penalty(objective_value, nutrients_total, dri, lambda_=1.0):
    R = calculate_penalty(nutrients_total, dri)
    return objective_value - lambda_ * R