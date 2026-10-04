import os
import runpy
import sqlite3
from pathlib import Path

BREAKFAST_GROUPS = [1, 4, 5, 7, 8, 11, 12, 13, 14, 20, 26, 27]
LUNCH_DINNER_GROUPS = [0, 2, 3, 6, 9, 10, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 28]
NON_VEGETARIAN_GROUPS = [2, 3, 15, 23, 28]

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv():
    """Load KEY=VALUE pairs from a .env file in the project root (existing env vars win)."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()


def get_connection():
    """Open a connection to the backend chosen by DB_BACKEND ('sqlite' by default, or 'mysql')."""
    backend = os.environ.get("DB_BACKEND", "sqlite").lower()
    if backend == "sqlite":
        path = Path(os.environ.get("SQLITE_PATH", ROOT / "data" / "diet.sqlite"))
        if not path.exists():
            # first run: build the SQLite file from the CSVs in data/
            runpy.run_path(str(ROOT / "scripts" / "build_sqlite.py"))["build"](path)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn
    if backend == "mysql":
        import mysql.connector
        return mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", "3306")),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "diet"),
        )
    raise ValueError(f"Unknown DB_BACKEND '{backend}' (use 'sqlite' or 'mysql')")


def _fetchall(sql, params=()):
    """Run a query and return a list of dict rows (queries are written with %s placeholders)."""
    conn = get_connection()
    try:
        if isinstance(conn, sqlite3.Connection):
            rows = conn.execute(sql.replace("%s", "?"), tuple(params)).fetchall()
            return [dict(row) for row in rows]
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


NUTRIENT_NAMES = ('Energy', 'Protein', 'Carbohydrate, by difference', 'Fiber, total dietary', 'Sodium, Na')
NAME_MAP = {
    'Energy': 'Energy',
    'Protein': 'Protein',
    'Carbohydrate, by difference': 'Carbohydrate',
    'Fiber, total dietary': 'Fiber_total_dietary',
    'Sodium, Na': 'Na'
}


def is_vegetarian(user_id):
    rows = _fetchall("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN uf.preference = -1 THEN 1 ELSE 0 END) as negative
        FROM user_foods uf
        JOIN foods f ON uf.foodId = f.id
        WHERE uf.userId = %s
        AND f.foodGroupId IN (2, 3, 15, 23, 28)
        AND uf.preference IS NOT NULL
    """, (user_id,))
    row = rows[0]
    if row['total'] == 0:
        return False
    ratio = row['negative'] / row['total']
    return ratio > 0.5

def get_food_data():
    rows = _fetchall("""
        SELECT id, name, foodGroupId, cost, preference, 
               preparingTime, cookingTime, co2
        FROM foods
    """)
    return {row['id']: row for row in rows}

def get_nutrients_data():
    names = ','.join(['%s'] * len(NUTRIENT_NAMES))
    rows = _fetchall(f"""
        SELECT fn.foodId, n.name, fn.quantity
        FROM food_nutrients fn
        JOIN nutrients n ON fn.nutrientId = n.id
        WHERE n.name IN ({names})
    """, NUTRIENT_NAMES)
    result = {}
    for row in rows:
        fid = row['foodId']
        if fid not in result:
            result[fid] = {}
        result[fid][NAME_MAP[row['name']]] = row['quantity']
    return result

def get_user_dri(user_id):
    names = ','.join(['%s'] * len(NUTRIENT_NAMES))
    rows = _fetchall(f"""
        SELECT n.name, d.RLL, d.RUL
        FROM dri d
        JOIN nutrients n ON d.nutrient_id = n.id
        JOIN user u ON u.age BETWEEN d.low_age AND d.up_age
            AND u.gender = d.gender
        WHERE u.id = %s
        AND n.name IN ({names})
    """, (user_id, *NUTRIENT_NAMES))
    return {NAME_MAP[row['name']]: {'RLL': row['RLL'], 'RUL': row['RUL']} for row in rows}

def get_user_preferences(user_id):
    rows = _fetchall("""
        SELECT foodId, preference
        FROM user_foods
        WHERE userId = %s AND preference IS NOT NULL
    """, (user_id,))
    return {row['foodId']: row['preference'] for row in rows}

def _food_ids_in_groups(groups):
    format_strings = ','.join(['%s'] * len(groups))
    rows = _fetchall(f"""
        SELECT id FROM foods
        WHERE foodGroupId IN ({format_strings})
    """, groups)
    return [row['id'] for row in rows]

def get_breakfast_food_ids(user_id):
    groups = BREAKFAST_GROUPS
    if is_vegetarian(user_id):
        groups = [g for g in BREAKFAST_GROUPS if g not in NON_VEGETARIAN_GROUPS]
    return _food_ids_in_groups(groups)

def get_lunch_dinner_food_ids(user_id):
    groups = LUNCH_DINNER_GROUPS
    if is_vegetarian(user_id):
        groups = [g for g in LUNCH_DINNER_GROUPS if g not in NON_VEGETARIAN_GROUPS]
    return _food_ids_in_groups(groups)

def get_food_ids_for_user(user_id):
    if is_vegetarian(user_id):
        format_strings = ','.join(['%s'] * len(NON_VEGETARIAN_GROUPS))
        rows = _fetchall(f"""
            SELECT id FROM foods
            WHERE foodGroupId NOT IN ({format_strings})
        """, NON_VEGETARIAN_GROUPS)
    else:
        rows = _fetchall("SELECT id FROM foods")
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