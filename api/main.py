"""NutriAI FastAPI service."""

from __future__ import annotations

import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse

from src.bmi import recommend_diet
from src.nutrition import NutritionFacts, get_nutrition
from src.predict import FoodPredictor
from src.reminders import ReminderService
from src.tracker import CalorieTracker, DailyTarget

ROOT_DIR = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = ROOT_DIR / "models" / "nutriai_resnet50.pth"
tracker = CalorieTracker(ROOT_DIR / "data_store" / "nutriai.sqlite3")
reminders = ReminderService()
predictor: FoodPredictor | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Load the optional trained model without preventing nutrition endpoints."""
    global predictor
    if CHECKPOINT_PATH.is_file():
        predictor = FoodPredictor(CHECKPOINT_PATH)
    yield
    reminders.stop()


app = FastAPI(title="NutriAI API", version="1.0.0", lifespan=lifespan)


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    """Serve the single-page NutriAI dashboard."""
    return FileResponse(ROOT_DIR / "api" / "static" / "index.html")


class BMIRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    height_cm: float = Field(gt=0, le=300)
    weight_kg: float = Field(gt=0, le=500)
    age: int = Field(gt=0, le=120)
    sex: Literal["female", "male"]
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"]
    goal: Literal["lose", "maintain", "gain"] = "maintain"


class LogRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    dish: str = Field(min_length=1, max_length=120)
    servings: float = Field(default=1.0, gt=0, le=20)
    nutrition: NutritionFacts | None = None


class ReminderRequest(BaseModel):
    times: list[str] = Field(min_length=1, max_length=8)
    message: str = Field(default="Remember to log your meal in NutriAI.", min_length=1, max_length=300)
    enabled: bool = True


@app.get("/health")
def health() -> dict[str, object]:
    """Report service readiness and whether image prediction is available."""
    return {"status": "ok", "model_loaded": predictor is not None, "device": str(predictor.device) if predictor else None}


@app.post("/predict")
async def predict(image: UploadFile = File(...)) -> dict[str, object]:
    """Classify an uploaded food image and include per-serving nutrition."""
    if predictor is None:
        raise HTTPException(503, "Model is not trained yet. Run src/train.py first.")
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(415, "Upload a valid image file.")
    try:
        content = await image.read()
        photo = Image.open(io.BytesIO(content))
        photo.verify()
        photo = Image.open(io.BytesIO(content))
        dish, confidence = predictor.predict(photo)
        return {"dish": dish, "confidence": confidence, "nutrition": get_nutrition(dish)}
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, "Could not read the uploaded image.") from exc


@app.post("/bmi")
def bmi(request: BMIRequest) -> dict[str, object]:
    """Calculate BMI, persist the daily target, and return diet guidance."""
    try:
        result = recommend_diet(**request.model_dump(exclude={"user_id"}))
        tracker.set_target(request.user_id, DailyTarget(result.calorie_target, result.protein_g, result.carbs_g, result.fat_g))
        return {"user_id": request.user_id, **result.to_dict()}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/log")
def log_food(request: LogRequest) -> dict[str, object]:
    """Log a model-supported dish or caller-supplied nutrition facts."""
    try:
        facts = request.nutrition or get_nutrition(request.dish)
        facts = facts.scaled(request.servings) if request.nutrition else get_nutrition(request.dish, request.servings)
        log_id = tracker.log_food(request.user_id, request.dish, facts, request.servings)
        return {"log_id": log_id, "dish": request.dish, "nutrition": facts, "summary": tracker.summary(request.user_id)}
    except (ValueError, KeyError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/summary")
def summary(user_id: str = "default") -> dict[str, object]:
    """Return today's consumed nutrition, target, and remaining values."""
    return tracker.summary(user_id)


@app.post("/reminders")
def configure_reminders(request: ReminderRequest) -> dict[str, object]:
    """Start or stop Windows desktop meal-logging notifications."""
    try:
        if not request.enabled:
            reminders.stop()
            return {"enabled": False, "times": []}
        times = reminders.start(request.times, request.message)
        return {"enabled": True, "times": times}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

