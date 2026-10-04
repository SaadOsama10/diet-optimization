"""Load data/*.csv into a MySQL database (created if missing) so the code can run with DB_BACKEND=mysql.

Credentials come from the DB_* environment variables (see .env.example). Existing tables with the same
names in the target database are dropped and recreated.
"""
import csv

import mysql.connector

from _db_env import DATA_DIR, SCHEMA_FILE, TABLES, mysql_config


def main():
    cfg = mysql_config()
    db = cfg.pop("database")
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4")
    cur.execute(f"USE `{db}`")
    for table in reversed(list(TABLES)):
        cur.execute(f"DROP TABLE IF EXISTS `{table}`")
    # drop comment lines first (they may contain ';'), then run each statement
    schema = "\n".join(l for l in SCHEMA_FILE.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--"))
    for stmt in schema.split(";"):
        if stmt.strip():
            cur.execute(stmt)
    for table, columns in TABLES.items():
        with open(DATA_DIR / f"{table}.csv", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            rows = [[None if v == "" else v for v in row] for row in reader]
        marks = ",".join(["%s"] * len(columns))
        cur.executemany(f"INSERT INTO `{table}` ({','.join(columns)}) VALUES ({marks})", rows)
        print(f"{table}: {len(rows)} rows")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
