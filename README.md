# Dual-Engine Music Generator

Deux moteurs, une interface (**Studio**) :

| Onglet | Moteur | Entrée | Sortie |
|--------|--------|--------|--------|
| **Audio** | MusicGen-small (préentraîné) | Texte en anglais | WAV |
| **MIDI** | LSTM (entraîné par vous) | Tonalité / mesure / seed ABC | ABC + MIDI |

## Démarrage rapide

```bash
pip install -r requirements.txt
python app.py
```

Puis ouvrez [http://localhost:7860](http://localhost:7860).

1. **Audio** — prêt immédiatement. Premier run : téléchargement MusicGen (~1–2 Go). Sur CPU, préférez 5–10 secondes.
2. **MIDI** — placez `best_model.pth` et `vocab.json` à la racine (voir entraînement ci-dessous).

## Entraîner le LSTM

### Google Colab (recommandé)

1. Ouvrez [`notebooks/train_lstm_colab.ipynb`](notebooks/train_lstm_colab.ipynb) (Runtime → GPU).
2. Exécutez toutes les cellules — le dataset Hugging Face se télécharge tout seul.
3. Téléchargez `lstm_weights.zip`, extrayez `best_model.pth` + `vocab.json` à la racine du projet.

### CPU local

```bash
jupyter notebook notebooks/train_lstm_local.ipynb
```

Environ 2–4 h sur un CPU moderne (40 % du dataset).

## Configuration

[`config/default_config.yaml`](config/default_config.yaml) — durée MusicGen, hyperparamètres LSTM, chemins, port Gradio.

## Structure

```
app.py                          # Interface Studio (Gradio)
config/default_config.yaml
notebooks/
  train_lstm_colab.ipynb        # Entraînement GPU Colab
  train_lstm_local.ipynb        # Entraînement CPU local
src/
  backends/                     # MusicGen + LSTM
  generation/ models/ utils/
tests/
```

## Tests

```bash
pytest
```

## Licence

MIT — voir [LICENSE](LICENSE).

MusicGen (Meta) a ses propres conditions d’usage ; vérifiez-les avant un usage commercial.
