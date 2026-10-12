"""
Interface web duale : MusicGen (audio) + LSTM (MIDI/ABC).

Usage:
    python app.py
"""

import logging
import socket
import sys

import gradio as gr

from src.backends.audio_musicgen import MusicGenBackend
from src.backends.symbolic_lstm import SymbolicLSTMBackend
from src.config import get_config
from src.utils.logger_setup import setup_logging

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

setup_logging()
logger = logging.getLogger(__name__)

config = get_config()
audio_backend = MusicGenBackend()
symbolic_backend = SymbolicLSTMBackend()

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg: #0b0e11;
  --bg-elevated: #12171c;
  --bg-panel: #171d24;
  --border: #2a333d;
  --text: #e8eef3;
  --muted: #8b9aab;
  --accent: #2dd4bf;
  --accent-dim: rgba(45, 212, 191, 0.14);
  --danger: #f07178;
  --radius: 14px;
}

.gradio-container {
  font-family: 'Outfit', system-ui, sans-serif !important;
  background:
    radial-gradient(1200px 500px at 10% -10%, rgba(45, 212, 191, 0.12), transparent 55%),
    radial-gradient(900px 400px at 100% 0%, rgba(56, 120, 180, 0.10), transparent 50%),
    var(--bg) !important;
  color: var(--text) !important;
  max-width: 1100px !important;
  margin: 0 auto !important;
  padding: 1.25rem 1rem 2.5rem !important;
}

.studio-hero {
  margin: 0.5rem 0 1.5rem;
  padding: 1.5rem 1.6rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: linear-gradient(145deg, var(--bg-panel), var(--bg-elevated));
}

.studio-hero h1 {
  margin: 0;
  font-size: clamp(1.6rem, 4vw, 2.2rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--text);
}

.studio-hero .tagline {
  margin: 0.55rem 0 0;
  color: var(--muted);
  font-size: 1.02rem;
  max-width: 42rem;
  line-height: 1.45;
}

.studio-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 1rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 500;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--muted);
}

.studio-badge.ok {
  border-color: rgba(45, 212, 191, 0.45);
  color: var(--accent);
  background: var(--accent-dim);
}

.studio-badge.warn {
  border-color: rgba(240, 113, 120, 0.4);
  color: #ffb4b8;
  background: rgba(240, 113, 120, 0.1);
}

#studio-tabs {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--bg-elevated) !important;
  overflow: hidden;
}

#studio-tabs > .tab-nav {
  background: var(--bg-panel) !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0.25rem !important;
  padding: 0.4rem !important;
}

#studio-tabs > .tab-nav button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  color: var(--muted) !important;
  border: none !important;
}

#studio-tabs > .tab-nav button.selected {
  background: var(--accent-dim) !important;
  color: var(--accent) !important;
}

.panel-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin: 0 0 0.75rem;
  font-weight: 600;
}

button.primary,
.generate-btn {
  background: var(--accent) !important;
  color: #042f2e !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  min-height: 48px !important;
  box-shadow: 0 8px 24px rgba(45, 212, 191, 0.25) !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

button.primary:hover,
.generate-btn:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 12px 28px rgba(45, 212, 191, 0.35) !important;
}

.abc-mono textarea,
.abc-mono input {
  font-family: 'IBM Plex Mono', ui-monospace, monospace !important;
  font-size: 0.86rem !important;
  line-height: 1.45 !important;
}

footer { display: none !important; }

@media (max-width: 768px) {
  .gradio-container {
    padding: 0.75rem 0.65rem 2rem !important;
  }
  .studio-hero {
    padding: 1.15rem 1.1rem;
  }
  #studio-tabs > .tab-nav button {
    font-size: 0.85rem !important;
    padding: 0.55rem 0.7rem !important;
  }
}
"""


def generate_audio(prompt, duration, seed):
    """Generate WAV from text via MusicGen."""
    try:
        seed_val = int(seed) if seed is not None and str(seed).strip() != "" else None
        result = audio_backend.generate(
            prompt=prompt,
            duration=float(duration),
            seed=seed_val,
        )
        return result.audio_path, result.message
    except Exception as exc:
        logger.exception("Audio generation failed")
        return None, f"Erreur audio : {exc}"


def generate_symbolic(temperature, length, key, meter, seed_text):
    """Generate ABC + MIDI via LSTM."""
    try:
        result = symbolic_backend.generate(
            temperature=float(temperature),
            length=int(length),
            key=key,
            meter=meter,
            seed=seed_text,
        )
        return result.abc_text or "", result.midi_path, result.message
    except Exception as exc:
        logger.exception("Symbolic generation failed")
        return "", None, f"Erreur MIDI : {exc}"


def find_free_port(start_port: int, max_attempts: int = 10):
    for offset in range(max_attempts):
        port = start_port + offset
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("", port))
                return port
        except OSError:
            continue
    return None


def build_interface():
    lstm_ready = symbolic_backend.weights_available()
    badge_class = "ok" if lstm_ready else "warn"
    badge_text = (
        "LSTM prêt — poids détectés"
        if lstm_ready
        else "LSTM : placez best_model.pth + vocab.json (voir notebooks/)"
    )

    with gr.Blocks(
        title="Studio — Générateur de musique",
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.teal,
            neutral_hue=gr.themes.colors.slate,
            font=[gr.themes.GoogleFont("Outfit"), "ui-sans-serif", "system-ui"],
            font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "ui-monospace"],
        ).set(
            body_background_fill="#0b0e11",
            block_background_fill="#171d24",
            block_border_color="#2a333d",
            block_label_text_color="#8b9aab",
            body_text_color="#e8eef3",
            button_primary_background_fill="#2dd4bf",
            button_primary_text_color="#042f2e",
            input_background_fill="#12171c",
            input_border_color="#2a333d",
        ),
        css=CUSTOM_CSS,
    ) as demo:
        gr.HTML(
            f"""
            <div class="studio-hero">
              <h1>Studio</h1>
              <p class="tagline">
                Deux moteurs dans une seule interface : MusicGen pour l’audio
                (texte → WAV), LSTM pour la partition éditable (ABC → MIDI).
              </p>
              <span class="studio-badge {badge_class}">{badge_text}</span>
            </div>
            """
        )

        with gr.Tabs(elem_id="studio-tabs"):
            with gr.Tab("Audio"):
                gr.Markdown(
                    '<p class="panel-label">Texte → WAV · MusicGen préentraîné</p>'
                    "Décrivez le style en anglais. Sur CPU, gardez **5–10 s**. "
                    "Le premier lancement télécharge le modèle (~1–2 Go)."
                )
                with gr.Row(equal_height=False):
                    with gr.Column(scale=5):
                        prompt = gr.Textbox(
                            label="Prompt",
                            placeholder="calm piano melody with soft strings",
                            lines=3,
                            max_lines=6,
                        )
                        with gr.Row():
                            duration = gr.Slider(
                                minimum=config.get("audio.min_duration", 5),
                                maximum=config.get("audio.max_duration", 15),
                                value=config.get("audio.default_duration", 8),
                                step=1,
                                label="Durée (s)",
                            )
                            audio_seed = gr.Number(
                                label="Seed",
                                value=None,
                                precision=0,
                                info="Optionnel, pour reproduire un résultat",
                            )
                        audio_btn = gr.Button(
                            "Générer l’audio",
                            variant="primary",
                            elem_classes=["generate-btn"],
                        )
                    with gr.Column(scale=6):
                        audio_status = gr.Textbox(
                            label="Statut",
                            interactive=False,
                            value="Prêt.",
                        )
                        audio_out = gr.Audio(
                            label="Résultat",
                            type="filepath",
                            show_download_button=True,
                        )

                gr.Examples(
                    label="Exemples rapides",
                    examples=[
                        ["calm piano melody with soft strings", 8, 42],
                        ["energetic electronic dance beat", 8, None],
                        ["sad jazz saxophone ballad", 10, 7],
                    ],
                    inputs=[prompt, duration, audio_seed],
                )
                audio_btn.click(
                    fn=generate_audio,
                    inputs=[prompt, duration, audio_seed],
                    outputs=[audio_out, audio_status],
                )

            with gr.Tab("MIDI"):
                gr.Markdown(
                    '<p class="panel-label">ABC → MIDI · LSTM entraîné par vous</p>'
                    "Génère une partition en notation ABC, puis un fichier MIDI. "
                    "Sans poids entraînés, cet onglet affiche un message d’aide."
                )
                with gr.Row(equal_height=False):
                    with gr.Column(scale=5):
                        with gr.Row():
                            temperature = gr.Slider(
                                minimum=config.get("generation.min_temperature", 0.3),
                                maximum=config.get("generation.max_temperature", 1.5),
                                value=config.get("generation.default_temperature", 0.8),
                                step=0.1,
                                label="Température",
                                info="Bas = stable, haut = créatif",
                            )
                            length = gr.Slider(
                                minimum=config.get("generation.min_length", 100),
                                maximum=config.get("generation.max_length", 800),
                                value=config.get("generation.default_length", 400),
                                step=50,
                                label="Longueur",
                            )
                        with gr.Row():
                            key = gr.Dropdown(
                                choices=config.get("generation.available_keys", []),
                                value=config.get("generation.default_key", "C"),
                                label="Tonalité",
                            )
                            meter = gr.Dropdown(
                                choices=config.get("generation.available_meters", []),
                                value=config.get("generation.default_meter", "4/4"),
                                label="Mesure",
                            )
                        seed_text = gr.Textbox(
                            label="Amorce ABC",
                            placeholder="Optionnel — ex.\nX:1\nL:1/8\nM:4/4\nK:C",
                            lines=3,
                            elem_classes=["abc-mono"],
                        )
                        midi_btn = gr.Button(
                            "Générer MIDI",
                            variant="primary",
                            elem_classes=["generate-btn"],
                        )
                    with gr.Column(scale=6):
                        midi_status = gr.Textbox(
                            label="Statut",
                            interactive=False,
                            value=(
                                "Prêt."
                                if lstm_ready
                                else "Poids absents — notebooks/train_lstm_colab.ipynb"
                            ),
                        )
                        abc_output = gr.Textbox(
                            label="Notation ABC",
                            lines=14,
                            max_lines=24,
                            elem_classes=["abc-mono"],
                        )
                        midi_output = gr.File(label="Télécharger MIDI")

                gr.Examples(
                    label="Exemples rapides",
                    examples=[
                        [0.7, 300, "C", "4/4", ""],
                        [0.9, 400, "G", "3/4", ""],
                        [1.0, 500, "Am", "4/4", ""],
                    ],
                    inputs=[temperature, length, key, meter, seed_text],
                )
                midi_btn.click(
                    fn=generate_symbolic,
                    inputs=[temperature, length, key, meter, seed_text],
                    outputs=[abc_output, midi_output, midi_status],
                )

    return demo


if __name__ == "__main__":
    interface_config = config.get("interface", {})
    default_port = interface_config.get("server_port", 7860)
    port = find_free_port(default_port) or default_port

    logger.info("Démarrage de l'interface sur le port %s", port)
    logger.info("MusicGen : %s", config.get("audio.model_id"))
    logger.info(
        "LSTM weights : %s",
        "présents" if symbolic_backend.weights_available() else "absents",
    )

    build_interface().launch(
        share=interface_config.get("share", False),
        server_name=interface_config.get("server_name", "0.0.0.0"),
        server_port=port,
    )
