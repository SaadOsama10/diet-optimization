import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="web01234",
        database="diet"
    )

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

if __name__ == "__main__":
    food_data = get_food_data()
    nutrients_data = get_nutrients_data()
    dri = get_user_dri(1)
    prefs = get_user_preferences(1)

    print(f"Foods: {len(food_data)}")
    print(f"Nutrients: {len(nutrients_data)}")
    print(f"DRI: {dri}")
    print(f"Preferences: {len(prefs)}")