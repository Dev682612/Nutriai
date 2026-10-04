"""SQLite persistence for food logs and daily nutrition summaries."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from src.nutrition import NutritionFacts


@dataclass(frozen=True)
class DailyTarget:
    """Daily calorie and macro budget."""
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class CalorieTracker:
    """Query-friendly local food diary stored in SQLite."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS food_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                    logged_at TEXT NOT NULL, dish TEXT NOT NULL, servings REAL NOT NULL,
                    calories REAL NOT NULL, protein_g REAL NOT NULL, carbs_g REAL NOT NULL, fat_g REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS daily_targets (
                    user_id TEXT PRIMARY KEY, calories REAL NOT NULL, protein_g REAL NOT NULL,
                    carbs_g REAL NOT NULL, fat_g REAL NOT NULL, updated_at TEXT NOT NULL
                );
            """)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(food_logs)")}
            if "servings" not in columns:
                conn.execute("ALTER TABLE food_logs ADD COLUMN servings REAL NOT NULL DEFAULT 1")

    def set_target(self, user_id: str, target: DailyTarget) -> None:
        """Create or update a user's daily target."""
        with closing(self._connect()) as conn, conn:
            conn.execute("""INSERT INTO daily_targets VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET calories=excluded.calories, protein_g=excluded.protein_g,
                carbs_g=excluded.carbs_g, fat_g=excluded.fat_g, updated_at=excluded.updated_at""",
                (user_id, *asdict(target).values(), datetime.now().isoformat(timespec="seconds")))

    def log_food(self, user_id: str, dish: str, nutrition: NutritionFacts, servings: float) -> int:
        """Record one consumed food item and return its row ID."""
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute("""INSERT INTO food_logs
                (user_id, logged_at, dish, servings, calories, protein_g, carbs_g, fat_g)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, datetime.now().isoformat(timespec="seconds"), dish, servings, *asdict(nutrition).values()))
            return int(cursor.lastrowid)

    def summary(self, user_id: str, for_date: date | None = None) -> dict[str, object]:
        """Return itemized totals and remaining budget for a calendar day."""
        day = for_date or date.today()
        with closing(self._connect()) as conn, conn:
            rows = conn.execute("SELECT * FROM food_logs WHERE user_id=? AND date(logged_at)=? ORDER BY logged_at", (user_id, day.isoformat())).fetchall()
            target_row = conn.execute("SELECT calories, protein_g, carbs_g, fat_g FROM daily_targets WHERE user_id=?", (user_id,)).fetchone()
        totals = {key: round(sum(float(row[key]) for row in rows), 1) for key in ("calories", "protein_g", "carbs_g", "fat_g")}
        target = dict(target_row) if target_row else None
        remaining = {key: round(float(target[key]) - totals[key], 1) for key in totals} if target else None
        return {"user_id": user_id, "date": day.isoformat(), "items": [dict(row) for row in rows], "totals": totals, "target": target, "remaining": remaining}

