import mysql.connector

BREAKFAST_GROUPS = [1, 4, 5, 7, 8, 11, 12, 13, 14, 20, 26, 27]
LUNCH_DINNER_GROUPS = [0, 2, 3, 6, 9, 10, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 28]
NON_VEGETARIAN_GROUPS = [2, 3, 15, 23, 28]

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="web01234",
        database="diet"
    )

def is_vegetarian(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN uf.preference = -1 THEN 1 ELSE 0 END) as negative
        FROM user_foods uf
        JOIN foods f ON uf.foodId = f.id
        WHERE uf.userId = %s
        AND f.foodGroupId IN (2, 3, 15, 23, 28)
        AND uf.preference IS NOT NULL
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row['total'] == 0:
        return False
    ratio = row['negative'] / row['total']
    return ratio > 0.5

def get_food_data():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, foodGroupId, cost, preference, 
               preparingTime, cookingTime, co2
        FROM foods
    """)
    rows = cursor.fetchall()
    conn.close()
    return {row['id']: row for row in rows}

def get_nutrients_data():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fn.foodId, n.name, fn.quantity
        FROM food_nutrients fn
        JOIN nutrients n ON fn.nutrientId = n.id
        WHERE n.name IN ('Energy', 'Protein', 'Carbohydrate, by difference', 'Fiber, total dietary', 'Sodium, Na')
    """)
    rows = cursor.fetchall()
    conn.close()
    name_map = {
        'Energy': 'Energy',
        'Protein': 'Protein',
        'Carbohydrate, by difference': 'Carbohydrate',
        'Fiber, total dietary': 'Fiber_total_dietary',
        'Sodium, Na': 'Na'
    }
    result = {}
    for row in rows:
        fid = row['foodId']
        if fid not in result:
            result[fid] = {}
        result[fid][name_map[row['name']]] = row['quantity']
    return result

def get_user_dri(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT n.name, d.RLL, d.RUL
        FROM dri d
        JOIN nutrients n ON d.nutrient_id = n.id
        JOIN user u ON u.age BETWEEN d.low_age AND d.up_age
            AND u.gender = d.gender
        WHERE u.id = %s
        AND n.name IN ('Energy', 'Protein', 'Carbohydrate, by difference', 'Fiber, total dietary', 'Sodium, Na')
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    name_map = {
        'Energy': 'Energy',
        'Protein': 'Protein',
        'Carbohydrate, by difference': 'Carbohydrate',
        'Fiber, total dietary': 'Fiber_total_dietary',
        'Sodium, Na': 'Na'
    }
    return {name_map[row['name']]: {'RLL': row['RLL'], 'RUL': row['RUL']} for row in rows}

def get_user_preferences(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT foodId, preference
        FROM user_foods
        WHERE userId = %s AND preference IS NOT NULL
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row['foodId']: row['preference'] for row in rows}

def get_breakfast_food_ids(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if is_vegetarian(user_id):
        veg_breakfast = [g for g in BREAKFAST_GROUPS if g not in NON_VEGETARIAN_GROUPS]
        format_strings = ','.join(['%s'] * len(veg_breakfast))
        cursor.execute(f"""
            SELECT id FROM foods
            WHERE foodGroupId IN ({format_strings})
        """, veg_breakfast)
    else:
        format_strings = ','.join(['%s'] * len(BREAKFAST_GROUPS))
        cursor.execute(f"""
            SELECT id FROM foods
            WHERE foodGroupId IN ({format_strings})
        """, BREAKFAST_GROUPS)
    rows = cursor.fetchall()
    conn.close()
    return [row['id'] for row in rows]

def get_lunch_dinner_food_ids(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if is_vegetarian(user_id):
        veg_lunch = [g for g in LUNCH_DINNER_GROUPS if g not in NON_VEGETARIAN_GROUPS]
        format_strings = ','.join(['%s'] * len(veg_lunch))
        cursor.execute(f"""
            SELECT id FROM foods
            WHERE foodGroupId IN ({format_strings})
        """, veg_lunch)
    else:
        format_strings = ','.join(['%s'] * len(LUNCH_DINNER_GROUPS))
        cursor.execute(f"""
            SELECT id FROM foods
            WHERE foodGroupId IN ({format_strings})
        """, LUNCH_DINNER_GROUPS)
    rows = cursor.fetchall()
    conn.close()
    return [row['id'] for row in rows]

def get_food_ids_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if is_vegetarian(user_id):
        format_strings = ','.join(['%s'] * len(NON_VEGETARIAN_GROUPS))
        cursor.execute(f"""
            SELECT id FROM foods
            WHERE foodGroupId NOT IN ({format_strings})
        """, NON_VEGETARIAN_GROUPS)
    else:
        cursor.execute("SELECT id FROM foods")
    rows = cursor.fetchall()
    conn.close()
    return [row['id'] for row in rows]

if __name__ == "__main__":
    print(f"User 1 vegetarian: {is_vegetarian(1)}")
    print(f"User 2 vegetarian: {is_vegetarian(2)}")
    food_data = get_food_data()
    nutrients_data = get_nutrients_data()
    dri = get_user_dri(1)
    prefs = get_user_preferences(1)
    breakfast_ids = get_breakfast_food_ids(1)
    lunch_ids = get_lunch_dinner_food_ids(1)

    print(f"Foods: {len(food_data)}")
    print(f"Nutrients: {len(nutrients_data)}")
    print(f"DRI: {dri}")
    print(f"Preferences: {len(prefs)}")
    print(f"Breakfast foods: {len(breakfast_ids)}")
    print(f"Lunch/Dinner foods: {len(lunch_ids)}")