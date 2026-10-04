"""Focused tests for NutriAI's dependency-light core behavior."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.bmi import calculate_bmi, recommend_diet
from src.nutrition import get_nutrition
from src.tracker import CalorieTracker, DailyTarget


class BMIAndNutritionTests(unittest.TestCase):
    def test_bmi_and_daily_recommendation(self) -> None:
        bmi, category = calculate_bmi(165, 60)
        recommendation = recommend_diet(165, 60, 25, "female", "moderate", "maintain")

        self.assertEqual((bmi, category), (22.0, "normal"))
        self.assertEqual(recommendation.bmi, bmi)
        self.assertGreater(recommendation.calorie_target, 0)

    def test_nutrition_scales_by_servings(self) -> None:
        one_serving = get_nutrition("pizza")
        two_servings = get_nutrition("Pizza", servings=2)

        self.assertEqual(two_servings.calories, one_serving.calories * 2)
        self.assertEqual(two_servings.protein_g, one_serving.protein_g * 2)


class TrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.database_path = Path(self.temp_dir.name) / "test.sqlite3"
        self.tracker = CalorieTracker(self.database_path)

    def test_target_and_food_log_appear_in_daily_summary(self) -> None:
        target = DailyTarget(2000, 150, 220, 67)
        facts = get_nutrition("pizza", servings=2)
        self.tracker.set_target("test-user", target)
        self.tracker.log_food("test-user", "pizza", facts, servings=2)

        summary = self.tracker.summary("test-user")

        self.assertEqual(summary["date"], date.today().isoformat())
        self.assertEqual(summary["target"]["calories"], target.calories)
        self.assertEqual(summary["totals"]["calories"], facts.calories)
        self.assertEqual(summary["remaining"]["calories"], round(target.calories - facts.calories, 1))
        self.assertEqual(summary["items"][0]["servings"], 2)

    def test_existing_database_gains_servings_column(self) -> None:
        legacy_path = self.database_path.with_name("legacy.sqlite3")
        connection = sqlite3.connect(legacy_path)
        connection.execute(
            """CREATE TABLE food_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                logged_at TEXT NOT NULL,
                dish TEXT NOT NULL,
                calories REAL NOT NULL,
                protein_g REAL NOT NULL,
                carbs_g REAL NOT NULL,
                fat_g REAL NOT NULL
            )"""
        )
        connection.execute(
            """INSERT INTO food_logs
                (user_id, logged_at, dish, calories, protein_g, carbs_g, fat_g)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("legacy-user", f"{date.today().isoformat()} 12:00:00", "pizza", 285, 12, 36, 10),
        )
        connection.commit()
        connection.close()

        tracker = CalorieTracker(legacy_path)
        summary = tracker.summary("legacy-user")

        self.assertEqual(summary["items"][0]["servings"], 1)


if __name__ == "__main__":
    unittest.main()