"""Model construction helpers for NutriAI."""

from __future__ import annotations

import torch
from torch import nn
from torchvision.models import ResNet50_Weights, resnet50


def get_device() -> torch.device:
    """Return a CUDA device when available, otherwise the CPU.

    MPS is intentionally not selected because this project targets Windows.
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    """Create a ResNet50 with a frozen feature extractor and new classifier."""
    if num_classes < 2:
        raise ValueError("num_classes must be at least 2")
    weights = ResNet50_Weights.DEFAULT if pretrained else None
    model = resnet50(weights=weights)
    for parameter in model.parameters():
        parameter.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model

