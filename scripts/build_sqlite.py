"""Build data/diet.sqlite from data/schema.sql and the CSV files in data/."""
import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _db_env import DATA_DIR, SCHEMA_FILE, TABLES


def build(path=DATA_DIR / "diet.sqlite"):
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    for table, columns in TABLES.items():
        with open(DATA_DIR / f"{table}.csv", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            rows = [[None if v == "" else v for v in row] for row in reader]
        marks = ",".join("?" * len(columns))
        conn.executemany(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({marks})", rows)
        print(f"{table}: {len(rows)} rows")
    conn.commit()
    conn.close()
    return path


if __name__ == "__main__":
    print("Built", build())
