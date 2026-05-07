import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="web01234",
        database="diet"
    )

def get_foods():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                   SELECT f.id, f.name, f.foodGroupId, f.cost,
                          f.preparingTime, f.cookingTime, f.co2
                   FROM foods f
                   """)
    foods = cursor.fetchall()
    conn.close()
    return foods

def get_user_preferences(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                   SELECT foodId, preference
                   FROM user_foods
                   WHERE userId = %s AND preference IS NOT NULL
                   """, (user_id,))
    prefs = cursor.fetchall()
    conn.close()
    return prefs

def get_food_nutrients():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                   SELECT foodId, nutrientId, value
                   FROM food_nutrients
                   """)
    nutrients = cursor.fetchall()
    conn.close()
    return nutrients

def get_dri(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                   SELECT d.nutrient_id, d.RLL, d.RUL
                   FROM dri d
                            JOIN user u ON u.age BETWEEN d.low_age AND d.up_age
                       AND u.gender = d.gender
                   WHERE u.id = %s
                     AND d.nutrient_id IN (
                       SELECT id FROM nutrients
                       WHERE name IN ('Energy', 'Protein', 'Carbohydrate',
                                      'Fiber_total_dietary', 'Na')
                   )
                   """, (user_id,))
    dri = cursor.fetchall()
    conn.close()
    return dri

if __name__ == "__main__":
    conn = get_connection()
    print(" Connected successfully!")
    conn.close()