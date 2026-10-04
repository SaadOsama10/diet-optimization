"""Shared helpers for the data scripts: paths, table definitions and MySQL settings from env vars."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_FILE = DATA_DIR / "schema.sql"

USED_NUTRIENTS = ("Energy", "Protein", "Carbohydrate, by difference", "Fiber, total dietary", "Sodium, Na")

# table -> columns, in the order they are written to / read from data/<table>.csv
TABLES = {
    "foods": ["id", "name", "foodGroupId", "cost", "preference", "preparingTime", "cookingTime", "co2"],
    "nutrients": ["id", "name"],
    "food_nutrients": ["foodId", "nutrientId", "quantity"],
    "dri": ["nutrient_id", "low_age", "up_age", "gender", "RLL", "RUL"],
    "user": ["id", "age", "gender"],
    "user_foods": ["userId", "foodId", "preference"],
}


def mysql_config():
    return dict(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "diet"),
    )
