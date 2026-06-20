# Music Generation with LSTM

Générateur de musique basé sur un réseau LSTM. Le modèle produit des compositions en notation ABC, enrichies harmoniquement puis converties en MIDI.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Entraînement

```bash
jupyter notebook Music_Generation.ipynb
```

Exécutez toutes les cellules. À la fin, vous disposez de `best_model.pth` et `vocab.json`.

Les paramètres sont centralisés dans `config/default_config.yaml` :

| Paramètre | Valeur par défaut |
|-----------|-------------------|
| embedding_dim | 128 |
| hidden_dim | 256 |
| num_layers | 2 |
| dataset_fraction | 0.4 |
| batch_size | 128 |
| seq_length | 64 |
| epochs | 12 |

### 2. Génération

```bash
python app.py
```

Interface disponible sur `http://localhost:7860`.

## Structure

```
├── app.py                      # Interface web Gradio
├── Music_Generation.ipynb      # Entraînement du modèle
├── config/default_config.yaml  # Configuration
├── src/
│   ├── models/lstm_model.py
│   ├── generation/music_generator.py
│   └── utils/
└── tests/
```

## Tests

```bash
pytest
```

## Fichiers générés (ignorés par Git)

- `best_model.pth`, `vocab.json` — produits à l'entraînement
- `*.abc`, `*.mid` — sorties de génération
- `training_history.png` — courbes d'entraînement

## Licence

MIT — voir [LICENSE](LICENSE).
