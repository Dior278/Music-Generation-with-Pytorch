# Music Generation with LSTM

A neural music generator that uses an LSTM model to create musical compositions in ABC notation, enriched with harmonic chords, arpeggios, and dynamic nuances.

## Features

- **Music Generation**: LSTM-based model for generating musical sequences
- **Harmonic Enrichment**: Automatic addition of chords and arpeggios
- **Dynamic Nuances**: Piano, forte, crescendo, diminuendo, and more
- **ABC Validation**: Ensures MIDI conversion compatibility
- **Web Interface**: Modern Gradio interface for easy interaction
- **Hardware Optimization**: Optimized for CPU training

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd music-generation

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Train the Model

Train the model using the Jupyter notebook:

```bash
jupyter notebook Music_Generation.ipynb
```

Run all cells in the notebook. The training process will:
- Download the ABC dataset automatically (~285,000 songs available)
- Train the LSTM model
- Save checkpoints and the best model
- Generate sample music

### Training Configuration

The notebook is optimized for CPU training with configurable parameters:

**Dataset Size (`DATASET_FRACTION`):**
- **Default: 0.4 (40%)** - Balanced speed/quality (~2-4 hours)
- **Fast training**: 0.2-0.3 (20-30%) - ~1-2 hours, lower quality
- **Better quality**: 0.6-0.8 (60-80%) - ~4-6 hours
- **Full dataset**: 1.0 (100%) - ~5-8 hours, best quality

**Model Architecture:**
- Optimized for CPU: 128 embedding dim, 256 hidden dim, 2 layers
- ~962,000 parameters (lightweight)
- Can be adjusted in the notebook for different quality/speed trade-offs

**Training Parameters:**
- **Epochs**: 12 (with early stopping)
- **Early stopping**: Stops if no improvement for 3 epochs
- **Batch size**: 128
- **Learning rate**: 0.001 (auto-reduced by scheduler)

**Expected Training Time:**
- Modern CPU (22 threads): 2-4 hours with default settings
- Adjust `DATASET_FRACTION` in the notebook to change training time

**What to Expect:**
- First epoch takes longest (model learning basics)
- Validation loss should decrease over time
- Best model automatically saved when validation improves
- Training stops early if no improvement detected

After training, you should have:
- `best_model.pth` - The trained model
- `vocab.json` - Character vocabulary
- Training checkpoints (if enabled)

### 2. Generate Music

Launch the web interface:

```bash
python quick_gradio_demo_modern.py
```

The interface will be available at `http://localhost:7860`

## Usage Guide

### Generation Parameters

- **Temperature** (0.5-1.5): Controls creativity and randomness
  - 0.5-0.7: Conservative, more predictable
  - 0.8-1.0: Balanced (recommended)
  - 1.1-1.5: Experimental, more creative

- **Length**: Number of characters to generate (typically 200-800)
- **Key**: Musical key for the composition (C, D, E, F, G, A, B, Am, Dm, etc.)
- **Meter**: Time signature (4/4, 3/4, 2/4, etc.)
- **Seed Text**: Optional starting sequence (leave empty for random start)

### Musical Enrichment

The system automatically enriches generated melodies with:

- **Harmonic Chords**: Added throughout the music (density: 0.9)
- **Arpeggios**: Classical-style arpeggios every 2 chords
- **Dynamic Nuances**: Piano, forte, crescendo, diminuendo variations
- **Articulations**: Staccatos, phrasing, and breathing pauses

### Export Options

- **ABC Notation**: View and copy the generated ABC text
- **MIDI File**: Download as MIDI for use in music software
- **Validation**: Automatic validation ensures MIDI compatibility

## Project Structure

```
music-generation/
├── src/
│   ├── generation/          # Music generation module
│   │   └── music_generator.py
│   ├── models/              # LSTM model architecture
│   │   └── lstm_model.py
│   ├── utils/               # Utilities
│   │   ├── abc_parser.py    # ABC notation parsing
│   │   ├── abc_validator.py # ABC validation and cleaning
│   │   ├── chord_enhancer.py # Harmonic enrichment
│   │   ├── midi_converter.py # ABC to MIDI conversion
│   │   ├── musical_expression.py # Dynamic nuances and articulations
│   │   └── validators.py    # Input validation
│   └── config.py            # Configuration management
├── config/
│   └── default_config.yaml  # Default configuration
├── Music_Generation.ipynb  # Training notebook
├── quick_gradio_demo_modern.py    # Modern web interface
└── requirements.txt         # Python dependencies
```

## Configuration

The project uses a YAML-based configuration system. Edit `config/default_config.yaml` to customize:

- Model paths
- Training parameters
- Generation defaults
- Logging settings

## Technologies

- **PyTorch**: Deep learning framework
- **music21**: Music notation and MIDI manipulation
- **Gradio**: Web interface framework

## Troubleshooting

### Model Not Found

If you get an error about missing model files:
1. Ensure you've trained the model first (see Quick Start)
2. Check that `best_model.pth` exists in the project root
3. Verify the model path in configuration

### MIDI Conversion Errors

The system includes automatic validation and cleaning:
- Duplicate headers are removed
- Invalid characters are filtered
- Format is normalized for music21 compatibility

If errors persist, check the logs for specific issues.

### Training Performance

The training is optimized for CPU:
- Multi-threading is enabled automatically
- Dataset sampling is used to reduce training time
- Early stopping prevents overfitting

### Import Errors

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Development

### Code Structure

The project follows a modular architecture:
- **Generation**: Core music generation logic
- **Models**: Neural network architectures
- **Utils**: Helper functions and utilities
- **Config**: Centralized configuration management

### Adding Features

To extend the project:
1. Add new modules in `src/utils/` for utilities
2. Modify `src/generation/music_generator.py` for generation logic
3. Update configuration in `config/default_config.yaml`
4. Add tests for new functionality

## File Notes

- **Model files** (`*.pth`): Not included in repository (too large)
- **Vocabulary** (`vocab.json`): Generated during training
- **Generated files** (`*.mid`, `*.abc`): Ignored by Git (see `.gitignore`)

## License

See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Please feel free to:
- Open issues for bugs or feature requests
- Submit pull requests with improvements
- Share feedback and suggestions

## Acknowledgments

- ABC dataset used for training
- music21 library for music notation handling
- PyTorch community for deep learning tools

## Citation

If you use this project in your research or work, please consider citing:

```bibtex
@software{music_generation_lstm,
  title = {Music Generation with LSTM},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/music-generation}
}
```
