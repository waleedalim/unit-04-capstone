"""Create and seed the sample enterprise SQLite database.

Run directly (``python -m src.db.init_db``) to (re)build
``src/db/enterprise.db`` with deterministic sample data, or import
``init_db`` to do the same programmatically (used by tests via a
temporary path).
"""
import random
import sqlite3
from pathlib import Path

from src import config

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

REGIONS = ["North", "South", "East", "West"]
QUARTER_MONTHS = {
    "Q1": [1, 2, 3],
    "Q2": [4, 5, 6],
    "Q3": [7, 8, 9],
    "Q4": [10, 11, 12],
}


def init_db(db_path: Path = config.DB_PATH, seed: int = 42) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.execute("DELETE FROM sales")
        conn.execute("DELETE FROM customers")

        for quarter, months in QUARTER_MONTHS.items():
            for month in months:
                for region in REGIONS:
                    for day in (5, 15, 25):
                        base = {"North": 12000, "South": 9000, "East": 10500, "West": 8000}[region]
                        revenue = round(base * (1 + rng.uniform(-0.15, 0.25)), 2)
                        conn.execute(
                            "INSERT INTO sales (sale_date, region, revenue, quarter) "
                            "VALUES (?, ?, ?, ?)",
                            (f"2024-{month:02d}-{day:02d}", region, revenue, quarter),
                        )

        for i in range(200):
            region = rng.choice(REGIONS)
            signup_month = rng.randint(1, 10)
            signup_date = f"2024-{signup_month:02d}-{rng.randint(1, 28):02d}"
            churn_date = None
            if rng.random() < 0.18:
                churn_month = min(signup_month + rng.randint(1, 3), 12)
                churn_date = f"2024-{churn_month:02d}-{rng.randint(1, 28):02d}"
            conn.execute(
                "INSERT INTO customers (region, signup_date, churn_date) VALUES (?, ?, ?)",
                (region, signup_date, churn_date),
            )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Seeded database at {config.DB_PATH}")
