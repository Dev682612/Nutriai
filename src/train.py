"""Train a configurable Food-101 subset classifier."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import torch
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

from src.dataset import DEFAULT_CLASSES, evaluation_transform, load_food101_subset, training_transform
from src.model import build_model, get_device


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, float]:
    """Return mean validation loss and accuracy."""
    criterion = nn.CrossEntropyLoss()
    model.eval()
    total_loss = correct = samples = 0
    with torch.inference_mode():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            output = model(images)
            total_loss += criterion(output, labels).item() * labels.size(0)
            correct += (output.argmax(1) == labels).sum().item()
            samples += labels.size(0)
    return total_loss / samples, correct / samples


def main() -> None:
    """Run the CLI training workflow."""
    parser = argparse.ArgumentParser(description="Train NutriAI on Food-101")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("models/nutriai_resnet50.pth"))
    parser.add_argument("--classes", nargs="+", default=DEFAULT_CLASSES)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--workers", type=int, default=0, help="Keep 0 for reliable Windows execution")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    if args.epochs <= 0 or args.batch_size <= 0:
        parser.error("epochs and batch-size must be positive")

    device = get_device()
    random.seed(42)
    torch.manual_seed(42)
    train_set = load_food101_subset(args.data_dir, "train", args.classes, training_transform(), args.download)
    val_set = load_food101_subset(args.data_dir, "test", args.classes, evaluation_transform(), args.download)
    loader_args = {"batch_size": args.batch_size, "num_workers": args.workers, "pin_memory": device.type == "cuda"}
    train_loader = DataLoader(train_set, shuffle=True, **loader_args)
    val_loader = DataLoader(val_set, shuffle=False, **loader_args)
    model = build_model(len(args.classes)).to(device)
    optimizer = AdamW(model.fc.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()
    best_accuracy = -1.0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(f"Training {len(args.classes)} classes on {device} ({len(train_set)} train / {len(val_set)} validation images)")
    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * labels.size(0)
        val_loss, accuracy = evaluate(model, val_loader, device)
        print(f"Epoch {epoch}/{args.epochs} | train_loss={running_loss / len(train_set):.4f} | val_loss={val_loss:.4f} | val_accuracy={accuracy:.2%}")
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            torch.save({"model_state": model.state_dict(), "class_names": list(args.classes), "val_accuracy": accuracy}, args.output)
            print(f"Saved best checkpoint to {args.output}")


if __name__ == "__main__":
    main()

