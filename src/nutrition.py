"""Nutrition lookups backed by a local JSON data source."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

DATA_FILE = Path(__file__).with_name("nutrition_data.json")


@dataclass(frozen=True)
class NutritionFacts:
    """Per-serving nutrition values."""

    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

    def scaled(self, servings: float) -> "NutritionFacts":
        """Return facts scaled by the requested number of servings."""
        if servings <= 0:
            raise ValueError("servings must be greater than zero")
        return NutritionFacts(**{key: round(value * servings, 1) for key, value in asdict(self).items()})


def _load_data() -> dict[str, NutritionFacts]:
    with DATA_FILE.open(encoding="utf-8") as file:
        raw_data = json.load(file)
    return {dish: NutritionFacts(**facts) for dish, facts in raw_data.items()}


NUTRITION_DB = _load_data()


def get_nutrition(dish: str, servings: float = 1.0) -> NutritionFacts:
    """Get local nutrition facts for a model dish label.

    This narrow function is the seam where a future USDA FoodData Central
    provider can be substituted without changing API or tracker code.
    """
    key = dish.strip().lower().replace(" ", "_")
    if key not in NUTRITION_DB:
        raise KeyError(f"Nutrition is unavailable for dish '{dish}'")
    return NUTRITION_DB[key].scaled(servings)

