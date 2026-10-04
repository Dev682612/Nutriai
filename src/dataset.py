"""Food-101 subset loading and image transforms."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms
from torchvision.datasets import Food101

DEFAULT_CLASSES = [
    "apple_pie",
    "caesar_salad",
    "cheese_plate",
    "chicken_curry",
    "chicken_wings",
    "french_fries",
    "fried_rice",
    "hamburger",
    "pizza",
    "spaghetti_bolognese",
]

IMAGE_SIZE = 224
NORMALIZE = transforms.Normalize(
    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
)


def training_transform() -> transforms.Compose:
    """Return augmentations suited to ImageNet-pretrained ResNet models."""
    return transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
        transforms.ToTensor(),
        NORMALIZE,
    ])


def evaluation_transform() -> transforms.Compose:
    """Return deterministic transforms for validation and inference."""
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        NORMALIZE,
    ])


class Food101Subset(Dataset[tuple[object, int]]):
    """Filtered Food-101 view which remaps labels to a compact class range."""

    def __init__(
        self,
        dataset: Food101,
        selected_classes: Sequence[str],
        indices: Sequence[int],
        transform: transforms.Compose,
    ) -> None:
        self.dataset = dataset
        self.class_names = list(selected_classes)
        self.indices = list(indices)
        self.transform = transform
        self.label_map = {
            dataset.class_to_idx[name]: new_label
            for new_label, name in enumerate(self.class_names)
        }

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, index: int) -> tuple[object, int]:
        image, original_label = self.dataset[self.indices[index]]
        if not isinstance(image, Image.Image):
            raise TypeError("Food101 did not return a PIL image")
        return self.transform(image), self.label_map[original_label]


def load_food101_subset(
    data_dir: Path,
    split: str,
    selected_classes: Sequence[str],
    transform: transforms.Compose,
    download: bool,
) -> Food101Subset:
    """Load an official Food-101 split and retain just selected classes."""
    dataset = Food101(root=str(data_dir), split=split, download=download)
    unknown = set(selected_classes) - set(dataset.classes)
    if unknown:
        raise ValueError(f"Unknown Food-101 classes: {sorted(unknown)}")
    requested_labels = {dataset.class_to_idx[name] for name in selected_classes}
    indices = [i for i, label in enumerate(dataset._labels) if label in requested_labels]
    if not indices:
        raise RuntimeError("No samples matched the selected Food-101 classes")
    return Food101Subset(dataset, selected_classes, indices, transform)
