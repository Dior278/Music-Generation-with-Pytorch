"""
Entraînement local du LSTM symbolique (ABC → MIDI).

Usage:
    python train_lstm.py

Les paramètres viennent de config/default_config.yaml.
Produit best_model.pth et vocab.json à la racine.
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from datasets import load_dataset
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import get_config
from src.models.lstm_model import MusicLSTM

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "training.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("train_lstm")


def extract_abc_notation(text: str) -> str:
    if "Assistant:" in text:
        text = text.split("Assistant:", 1)[1].strip()
    return text.replace("</s>", "").strip()


class MusicDataset(Dataset):
    def __init__(self, songs, char2idx, seq_length: int):
        self.char2idx = char2idx
        self.sequences = []
        step = max(1, seq_length // 2)
        for song in songs:
            if len(song) <= seq_length:
                continue
            for i in range(0, len(song) - seq_length, step):
                seq = song[i : i + seq_length + 1]
                if len(seq) == seq_length + 1:
                    self.sequences.append(seq)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        seq = self.sequences[idx]
        x = [self.char2idx[c] for c in seq[:-1]]
        y = [self.char2idx[c] for c in seq[1:]]
        return torch.tensor(x), torch.tensor(y)


def train_epoch(model, loader, criterion, optimizer, device, vocab_size, clip):
    model.train()
    total = 0.0
    for inputs, targets in tqdm(loader, desc="train", leave=False):
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs, _ = model(inputs)
        loss = criterion(outputs.reshape(-1, vocab_size), targets.reshape(-1))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        optimizer.step()
        total += loss.item()
    return total / max(len(loader), 1)


@torch.no_grad()
def validate(model, loader, criterion, device, vocab_size):
    model.eval()
    total = 0.0
    for inputs, targets in loader:
        inputs, targets = inputs.to(device), targets.to(device)
        outputs, _ = model(inputs)
        loss = criterion(outputs.reshape(-1, vocab_size), targets.reshape(-1))
        total += loss.item()
    return total / max(len(loader), 1)


def main():
    config = get_config()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cpu":
        torch.set_num_threads(os.cpu_count() or 1)

    epochs = int(config.get("training.epochs", 12))
    batch_size = int(config.get("training.batch_size", 128))
    lr = float(config.get("training.learning_rate", 0.001))
    seq_length = int(config.get("training.seq_length", 64))
    fraction = float(config.get("training.dataset_fraction", 0.6))
    train_split = float(config.get("training.train_split", 0.95))
    clip = float(config.get("training.gradient_clip", 1.0))
    patience_limit = int(config.get("training.early_stopping_patience", 3))
    sched_patience = int(config.get("training.scheduler_patience", 2))
    sched_factor = float(config.get("training.scheduler_factor", 0.5))

    emb = int(config.get("model.embedding_dim", 128))
    hid = int(config.get("model.hidden_dim", 256))
    layers = int(config.get("model.num_layers", 2))
    dropout = float(config.get("model.dropout", 0.3))

    model_path = ROOT / config.get("paths.model", "best_model.pth")
    vocab_path = ROOT / config.get("paths.vocab", "vocab.json")

    logger.info("Device: %s", device)
    logger.info(
        "Config: epochs=%s batch=%s seq=%s fraction=%.0f%%",
        epochs,
        batch_size,
        seq_length,
        fraction * 100,
    )

    logger.info("Loading dataset Seeker38/music_abc_notation ...")
    dataset = load_dataset("Seeker38/music_abc_notation", split="train")
    abc_songs = [extract_abc_notation(item["output"]) for item in dataset]
    abc_songs = [s for s in abc_songs if 50 < len(s) < 2000]
    logger.info("Songs after filter: %s", len(abc_songs))

    all_text = "\n".join(abc_songs)
    vocab = sorted(set(all_text))
    vocab_size = len(vocab)
    char2idx = {c: i for i, c in enumerate(vocab)}
    idx2char = {i: c for i, c in enumerate(vocab)}

    vocab_info = {
        "vocab": vocab,
        "char2idx": char2idx,
        "idx2char": {int(k): v for k, v in idx2char.items()},
        "vocab_size": vocab_size,
    }
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocab_info, f, ensure_ascii=False, indent=2)
    logger.info("Vocabulary saved (%s chars) -> %s", vocab_size, vocab_path.name)

    random.seed(42)
    n_sample = max(1, int(len(abc_songs) * fraction))
    sampled = random.sample(abc_songs, n_sample)
    split = int(train_split * len(sampled))
    train_ds = MusicDataset(sampled[:split], char2idx, seq_length)
    val_ds = MusicDataset(sampled[split:], char2idx, seq_length)

    num_workers = 0 if sys.platform == "win32" else min(4, os.cpu_count() or 1)
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=num_workers,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        drop_last=True,
        num_workers=num_workers,
    )
    logger.info(
        "Sequences train=%s val=%s workers=%s",
        len(train_ds),
        len(val_ds),
        num_workers,
    )

    model = MusicLSTM(
        vocab_size=vocab_size,
        embedding_dim=emb,
        hidden_dim=hid,
        num_layers=layers,
        dropout=dropout,
    ).to(device)
    logger.info("Parameters: %s", f"{model.get_num_parameters():,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=sched_factor, patience=sched_patience
    )

    history = {"train_loss": [], "val_loss": [], "learning_rates": []}
    best_val = float("inf")
    patience = 0

    # Backup previous weights if present
    if model_path.exists():
        backup = model_path.with_suffix(".pth.bak")
        model_path.replace(backup)
        logger.info("Previous model backed up -> %s", backup.name)

    for epoch in range(epochs):
        logger.info("Epoch %s/%s", epoch + 1, epochs)
        train_loss = train_epoch(
            model, train_loader, criterion, optimizer, device, vocab_size, clip
        )
        val_loss = validate(model, val_loader, criterion, device, vocab_size)
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["learning_rates"].append(current_lr)

        logger.info(
            "  train=%.4f  val=%.4f  lr=%.6f",
            train_loss,
            val_loss,
            current_lr,
        )

        if val_loss < best_val:
            best_val = val_loss
            patience = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_loss": val_loss,
                    "vocab_size": vocab_size,
                },
                model_path,
            )
            logger.info("  best model saved -> %s", model_path.name)
        else:
            patience += 1
            logger.info("  no improvement (%s/%s)", patience, patience_limit)
            if patience >= patience_limit:
                logger.info("Early stopping.")
                break

    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history["train_loss"], label="train")
    plt.plot(history["val_loss"], label="val")
    plt.legend()
    plt.title("Loss")
    plt.subplot(1, 2, 2)
    plt.plot(history["learning_rates"])
    plt.title("Learning rate")
    plt.tight_layout()
    plt.savefig(ROOT / "training_history.png", dpi=120)
    logger.info("Training finished. Best val loss: %.4f", best_val)
    logger.info("Files: %s , %s , training_history.png", model_path.name, vocab_path.name)


if __name__ == "__main__":
    main()
