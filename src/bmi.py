"""BMI, energy target, and diet recommendation calculations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Sex = Literal["female", "male"]
Goal = Literal["lose", "maintain", "gain"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]

ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
    "active": 1.725, "very_active": 1.9,
}
GOAL_ADJUSTMENTS: dict[Goal, int] = {"lose": -500, "maintain": 0, "gain": 300}


@dataclass(frozen=True)
class DietRecommendation:
    """Calculated health guidance for a single person."""

    bmi: float
    category: str
    calorie_target: int
    protein_g: int
    carbs_g: int
    fat_g: int
    recommendation: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation."""
        return asdict(self)


def calculate_bmi(height_cm: float, weight_kg: float) -> tuple[float, str]:
    """Calculate BMI and its standard adult category."""
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("height_cm and weight_kg must be positive")
    bmi = weight_kg / (height_cm / 100) ** 2
    category = "underweight" if bmi < 18.5 else "normal" if bmi < 25 else "overweight" if bmi < 30 else "obese"
    return round(bmi, 1), category


def recommend_diet(
    height_cm: float, weight_kg: float, age: int, sex: Sex,
    activity_level: ActivityLevel, goal: Goal,
) -> DietRecommendation:
    """Use Mifflin-St Jeor and practical macro splits to make a diet target."""
    if age <= 0:
        raise ValueError("age must be positive")
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")
    if activity_level not in ACTIVITY_MULTIPLIERS or goal not in GOAL_ADJUSTMENTS:
        raise ValueError("Invalid activity level or goal")
    bmi, category = calculate_bmi(height_cm, weight_kg)
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if sex == "male" else -161)
    target = max(1200, round(base * ACTIVITY_MULTIPLIERS[activity_level] + GOAL_ADJUSTMENTS[goal]))
    protein_g = round(target * 0.30 / 4)
    carbs_g = round(target * 0.40 / 4)
    fat_g = round(target * 0.30 / 9)
    messages = {
        "underweight": "Prioritize nutrient-dense meals, regular meals, and gradual healthy weight gain guidance.",
        "normal": "Maintain a balanced plate with vegetables, lean protein, whole grains, and consistent activity.",
        "overweight": "Favor high-fiber foods and lean protein; aim for sustainable portions and gradual progress.",
        "obese": "Focus on a sustainable calorie deficit, filling high-fiber foods, and professional support when useful.",
    }
    return DietRecommendation(bmi, category, target, protein_g, carbs_g, fat_g, messages[category])

