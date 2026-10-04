"""Export the minimal, sanitized dataset from the original MySQL `diet` database to data/*.csv.

Only the columns the optimizer reads are exported. User names, usernames and password hashes are never
selected. Credentials come from the DB_* environment variables (see .env.example).
"""
import csv

import mysql.connector

from _db_env import DATA_DIR, TABLES, USED_NUTRIENTS, mysql_config

NUTRIENT_FILTER = "(" + ",".join(["%s"] * len(USED_NUTRIENTS)) + ")"


def queries():
    cols = lambda t, prefix="": ", ".join(f"{prefix}{c}" for c in TABLES[t])
    return {
        "foods": (f"SELECT {cols('foods')} FROM foods ORDER BY id", ()),
        "nutrients": (f"SELECT {cols('nutrients')} FROM nutrients WHERE name IN {NUTRIENT_FILTER} ORDER BY id", USED_NUTRIENTS),
        "food_nutrients": (
            "SELECT fn.foodId, fn.nutrientId, fn.quantity FROM food_nutrients fn "
            f"JOIN nutrients n ON fn.nutrientId = n.id WHERE n.name IN {NUTRIENT_FILTER} ORDER BY fn.foodId, fn.nutrientId",
            USED_NUTRIENTS),
        "dri": (
            "SELECT d.nutrient_id, d.low_age, d.up_age, LOWER(d.gender), d.RLL, d.RUL FROM dri d "
            f"JOIN nutrients n ON d.nutrient_id = n.id WHERE n.name IN {NUTRIENT_FILTER} "
            "ORDER BY d.nutrient_id, d.gender, d.low_age", USED_NUTRIENTS),
        # gender is lower-cased: MySQL compares it case-insensitively, SQLite does not
        "user": ("SELECT id, age, LOWER(gender) FROM user ORDER BY id", ()),
        "user_foods": (f"SELECT {cols('user_foods')} FROM user_foods ORDER BY userId, foodId", ()),
    }


def main():
    conn = mysql.connector.connect(**mysql_config())
    cur = conn.cursor()
    DATA_DIR.mkdir(exist_ok=True)
    for table, (sql, params) in queries().items():
        cur.execute(sql, params)
        rows = cur.fetchall()
        with open(DATA_DIR / f"{table}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(TABLES[table])
            w.writerows(rows)
        print(f"{table}: {len(rows)} rows")
    conn.close()


if __name__ == "__main__":
    main()
