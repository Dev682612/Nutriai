"""Single-image inference for a trained NutriAI model."""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image

from src.dataset import evaluation_transform
from src.model import build_model, get_device


class FoodPredictor:
    """Loads a checkpoint once and provides safe image classification."""

    def __init__(self, checkpoint_path: Path) -> None:
        if not checkpoint_path.is_file():
            raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")
        self.device = get_device()
        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        self.class_names: list[str] = checkpoint["class_names"]
        self.model = build_model(len(self.class_names), pretrained=False).to(self.device)
        self.model.load_state_dict(checkpoint["model_state"])
        self.model.eval()
        self.transform = evaluation_transform()

    @torch.inference_mode()
    def predict(self, image: Image.Image) -> tuple[str, float]:
        """Return the highest-probability dish label and confidence."""
        tensor = self.transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        probabilities = torch.softmax(self.model(tensor), dim=1)[0]
        confidence, index = torch.max(probabilities, dim=0)
        return self.class_names[int(index)], round(float(confidence), 4)

