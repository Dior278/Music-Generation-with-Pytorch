# Dual-Engine Music Generator

Générateur de musique à **deux moteurs** :

| Mode | Technologie | Sortie | Entraînement |
|------|-------------|--------|--------------|
| **Audio** | MusicGen-small (préentraîné, Hugging Face) | WAV | Aucun — téléchargé au premier usage |
| **MIDI** | LSTM caractère-par-caractère sur notation ABC | ABC + MIDI | Vous entraînez (Colab GPU ou CPU local) |

## Installation

```bash
pip install -r requirements.txt
```

## Lancer l'interface

```bash
python app.py
```

Ouvrez `http://localhost:7860`.

- Onglet **Audio** : décrivez la musique en anglais (ex. `calm piano melody with soft strings`). Premier lancement = téléchargement de MusicGen (~1–2 Go). Sur CPU, préférez 5–10 secondes.
- Onglet **MIDI** : nécessite `best_model.pth` + `vocab.json` à la racine (voir ci-dessous).

## Entraîner le LSTM (piste MIDI)

### Option recommandée : Google Colab (GPU)

1. Ouvrez [`notebooks/train_lstm_colab.ipynb`](notebooks/train_lstm_colab.ipynb) dans Colab (Runtime → GPU).
2. Exécutez toutes les cellules. Le dataset Hugging Face se télécharge tout seul.
3. Téléchargez `lstm_weights.zip` (`best_model.pth` + `vocab.json`).
4. Placez les deux fichiers à la racine de ce dépôt.

### Option locale (CPU)

```bash
jupyter notebook Music_Generation.ipynb
```

Entraînement typique : 2–4 h sur CPU moderne (40 % du dataset).

## Configuration

[`config/default_config.yaml`](config/default_config.yaml) — chemins, hyperparamètres LSTM, durée MusicGen, ports Gradio.

## Structure

```
├── app.py                         # Interface Gradio duale
├── Music_Generation.ipynb         # Entraînement LSTM local
├── notebooks/train_lstm_colab.ipynb
├── config/default_config.yaml
├── src/
│   ├── backends/                  # MusicGen + LSTM
│   ├── generation/
│   ├── models/
│   └── utils/
└── tests/
```

## Tests

```bash
pytest
```

Les tests mockent MusicGen (aucun téléchargement Hugging Face en CI).

## Licence

MIT — voir [LICENSE](LICENSE).

MusicGen (Meta) est fourni sous sa propre licence non commerciale pour certains usages ; vérifiez les conditions Hugging Face avant un déploiement commercial.
