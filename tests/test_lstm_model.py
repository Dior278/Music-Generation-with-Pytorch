"""Tests for the LSTM model."""

import torch

from src.models.lstm_model import MusicLSTM


def test_music_lstm_forward_shape():
    model = MusicLSTM(vocab_size=50, embedding_dim=32, hidden_dim=64, num_layers=2, dropout=0.0)
    x = torch.randint(0, 50, (2, 10))
    output, hidden = model(x)

    assert output.shape == (2, 10, 50)
    assert hidden is not None


def test_music_lstm_autoregressive_step():
    model = MusicLSTM(vocab_size=20, embedding_dim=16, hidden_dim=32, num_layers=2, dropout=0.0)
    model.eval()

    x = torch.randint(0, 20, (1, 5))
    with torch.no_grad():
        output, hidden = model(x)
        next_token = torch.randint(0, 20, (1, 1))
        output2, hidden2 = model(next_token, hidden)

    assert output2.shape == (1, 1, 20)
    assert hidden2 is not None


def test_get_num_parameters():
    model = MusicLSTM(vocab_size=100)
    assert model.get_num_parameters() > 0
