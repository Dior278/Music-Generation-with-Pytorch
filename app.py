"""
Studio — interface duale MusicGen + LSTM, avec lecteur MIDI et thème clair/sombre.

Usage:
    python app.py
"""

from __future__ import annotations

import base64
import logging
import socket
import sys
from pathlib import Path

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

HEAD_HTML = """
<script src="https://cdn.jsdelivr.net/combine/npm/tone@14.7.77,npm/@magenta/music@1.23.1/es6/core.js,npm/html-midi-player@1.5.0"></script>
"""

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;0,800;1,500&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --font-display: 'Playfair Display', 'Times New Roman', Times, serif;
  --font-body: 'Libre Baskerville', 'Times New Roman', Times, Georgia, serif;
  --font-mono: 'JetBrains Mono', 'Courier New', monospace;
  --bg: #090b0f;
  --bg-elevated: #11151c;
  --bg-panel: #161b24;
  --border: #2c3542;
  --text: #f2f5f8;
  --muted: #9aa8b8;
  --accent: #ff6b4a;
  --accent-2: #3ecfb2;
  --accent-dim: rgba(255, 107, 74, 0.16);
  --radius: 18px;
  --shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
}

html.theme-light {
  --bg: #f4f1ea;
  --bg-elevated: #ffffff;
  --bg-panel: #faf8f4;
  --border: #e2ddd3;
  --text: #17140f;
  --muted: #6d655a;
  --accent: #d4552f;
  --accent-2: #0f7a68;
  --accent-dim: rgba(212, 85, 47, 0.12);
  --shadow: 0 18px 40px rgba(40, 30, 20, 0.08);
}

.gradio-container {
  font-family: var(--font-body) !important;
  background:
    radial-gradient(900px 420px at 0% 0%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 55%),
    radial-gradient(700px 360px at 100% 10%, color-mix(in srgb, var(--accent-2) 14%, transparent), transparent 50%),
    var(--bg) !important;
  color: var(--text) !important;
  max-width: 1120px !important;
  margin: 0 auto !important;
  padding: 1.1rem 1rem 2.8rem !important;
}

.gradio-container label,
.gradio-container button,
.gradio-container .prose,
.gradio-container p,
.gradio-container span {
  font-family: var(--font-body) !important;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.studio-hero {
  flex: 1;
  padding: 1.55rem 1.7rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: linear-gradient(160deg, var(--bg-panel), var(--bg-elevated));
  box-shadow: var(--shadow);
}

.studio-hero h1 {
  margin: 0;
  font-family: var(--font-display) !important;
  font-size: clamp(2.35rem, 6vw, 3.4rem);
  font-weight: 700;
  font-style: italic;
  letter-spacing: -0.02em;
  line-height: 1.05;
  color: var(--text);
}

.studio-hero .tagline {
  margin: 0.7rem 0 0;
  color: var(--muted);
  font-family: var(--font-body) !important;
  font-size: 1.05rem;
  max-width: 38rem;
  line-height: 1.65;
}

.studio-badge {
  display: inline-flex;
  margin-top: 1rem;
  padding: 0.38rem 0.8rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  border: 1px solid var(--border);
  color: var(--muted);
  background: var(--bg);
}

.studio-badge.ok {
  border-color: color-mix(in srgb, var(--accent-2) 50%, var(--border));
  color: var(--accent-2);
  background: color-mix(in srgb, var(--accent-2) 12%, transparent);
}

.studio-badge.warn {
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
  color: var(--accent);
  background: var(--accent-dim);
}

#theme-toggle {
  flex-shrink: 0;
  border: 1px solid var(--border) !important;
  background: var(--bg-elevated) !important;
  color: var(--text) !important;
  border-radius: 999px !important;
  padding: 0.7rem 1.05rem !important;
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  font-style: italic !important;
  font-size: 1rem !important;
  min-height: 46px !important;
  cursor: pointer;
  box-shadow: none !important;
}

#theme-toggle:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}

#studio-tabs {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--bg-elevated) !important;
  overflow: hidden;
  box-shadow: var(--shadow);
}

#studio-tabs > .tab-nav {
  background: var(--bg-panel) !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0.35rem !important;
  padding: 0.45rem !important;
}

#studio-tabs > .tab-nav button {
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  font-style: italic !important;
  border-radius: 12px !important;
  color: var(--muted) !important;
  border: none !important;
  letter-spacing: 0.01em;
  font-size: 1.05rem !important;
}

#studio-tabs > .tab-nav button.selected {
  background: var(--accent-dim) !important;
  color: var(--accent) !important;
}

.panel-label {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-style: italic;
  letter-spacing: 0.04em;
  color: var(--muted);
  margin: 0 0 0.65rem;
  font-weight: 700;
}

button.primary,
.generate-btn {
  background: var(--accent) !important;
  color: #1a0b07 !important;
  border: none !important;
  border-radius: 14px !important;
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  font-style: italic !important;
  font-size: 1.15rem !important;
  min-height: 52px !important;
  letter-spacing: 0.01em;
  box-shadow: 0 10px 28px color-mix(in srgb, var(--accent) 35%, transparent) !important;
}

.abc-mono textarea,
.abc-mono input {
  font-family: var(--font-mono) !important;
  font-size: 0.84rem !important;
  line-height: 1.45 !important;
}

.midi-wrap {
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 0.9rem;
  background: var(--bg-panel);
}

.midi-wrap midi-player {
  width: 100%;
  display: block;
}

.midi-wrap midi-visualizer {
  width: 100%;
  display: block;
  margin-top: 0.75rem;
  background: transparent;
  overflow: auto;
}

.player-empty {
  margin: 0;
  padding: 1.2rem;
  border: 1px dashed var(--border);
  border-radius: 14px;
  color: var(--muted);
  font-size: 0.95rem;
  text-align: center;
}

footer { display: none !important; }

@media (max-width: 768px) {
  .topbar { flex-direction: column; }
  #theme-toggle { width: 100%; }
  .studio-hero { padding: 1.2rem 1.15rem; }
}
"""

def midi_player_html(midi_path: str | None) -> str:
    """Build an in-browser MIDI player (Magenta html-midi-player)."""
    if not midi_path:
        return '<p class="player-empty">Générez un MIDI pour l’écouter ici.</p>'

    path = Path(midi_path)
    if not path.exists():
        return '<p class="player-empty">Fichier MIDI introuvable.</p>'

    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    src = f"data:audio/midi;base64,{payload}"
    return f"""
    <div class="midi-wrap">
      <midi-player src="{src}"
        sound-font="https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus"
        style="width:100%;">
      </midi-player>
      <midi-visualizer type="piano-roll" src="{src}"></midi-visualizer>
    </div>
    """


def generate_audio(prompt, duration, seed):
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
    try:
        result = symbolic_backend.generate(
            temperature=float(temperature),
            length=int(length),
            key=key,
            meter=meter,
            seed=seed_text,
        )
        player = midi_player_html(result.midi_path)
        return result.abc_text or "", result.midi_path, player, result.message
    except Exception as exc:
        logger.exception("Symbolic generation failed")
        empty = midi_player_html(None)
        return "", None, empty, f"Erreur MIDI : {exc}"


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
        "LSTM prêt"
        if lstm_ready
        else "LSTM : best_model.pth + vocab.json manquants"
    )

    theme = gr.themes.Base(
        primary_hue=gr.themes.colors.orange,
        neutral_hue=gr.themes.colors.zinc,
        font=[
            gr.themes.GoogleFont("Libre Baskerville"),
            "Times New Roman",
            "Times",
            "Georgia",
            "serif",
        ],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "Courier New", "monospace"],
    ).set(
        body_background_fill="#090b0f",
        block_background_fill="#161b24",
        block_border_color="#2c3542",
        block_label_text_color="#9aa8b8",
        body_text_color="#f2f5f8",
        button_primary_background_fill="#ff6b4a",
        button_primary_text_color="#1a0b07",
        input_background_fill="#11151c",
        input_border_color="#2c3542",
    )

    with gr.Blocks(title="Studio") as demo:
        gr.HTML(
            f"""
            <div class="topbar">
              <div class="studio-hero">
                <h1>Studio</h1>
                <p class="tagline">
                  Composez en un clic : audio génératif (MusicGen) ou partition
                  MIDI éditable (LSTM). Écoutez le résultat directement ici.
                </p>
                <span class="studio-badge {badge_class}">{badge_text}</span>
              </div>
              <button type="button" id="theme-toggle"
                onclick="document.documentElement.classList.toggle('theme-light');this.textContent=document.documentElement.classList.contains('theme-light')?'Mode sombre':'Mode clair';">
                Mode clair
              </button>
            </div>
            """
        )

        with gr.Tabs(elem_id="studio-tabs"):
            with gr.Tab("Audio"):
                gr.Markdown(
                    '<p class="panel-label">Texte → WAV</p>\n'
                    "Prompt en anglais. Sur CPU, **5–10 s** suffisent. "
                    "Premier lancement = téléchargement MusicGen."
                )
                with gr.Row():
                    with gr.Column(scale=5):
                        prompt = gr.Textbox(
                            label="Prompt",
                            placeholder="calm piano melody with soft strings",
                            lines=3,
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
                            )
                        audio_btn = gr.Button(
                            "Générer l’audio",
                            variant="primary",
                            elem_classes=["generate-btn"],
                        )
                    with gr.Column(scale=6):
                        audio_status = gr.Textbox(
                            label="Statut", interactive=False, value="Prêt."
                        )
                        audio_out = gr.Audio(label="Écouter", type="filepath")

                gr.Examples(
                    label="Exemples",
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
                    '<p class="panel-label">ABC → MIDI + lecture</p>\n'
                    "Générez une partition, **écoutez-la** dans le lecteur, "
                    "puis téléchargez le `.mid`."
                )
                with gr.Row():
                    with gr.Column(scale=5):
                        with gr.Row():
                            temperature = gr.Slider(
                                minimum=config.get("generation.min_temperature", 0.3),
                                maximum=config.get("generation.max_temperature", 1.5),
                                value=config.get("generation.default_temperature", 0.8),
                                step=0.1,
                                label="Température",
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
                            placeholder="Optionnel",
                            lines=3,
                            elem_classes=["abc-mono"],
                        )
                        midi_btn = gr.Button(
                            "Générer et écouter",
                            variant="primary",
                            elem_classes=["generate-btn"],
                        )
                    with gr.Column(scale=6):
                        midi_status = gr.Textbox(
                            label="Statut",
                            interactive=False,
                            value="Prêt." if lstm_ready else badge_text,
                        )
                        midi_player = gr.HTML(
                            value=midi_player_html(None),
                            label="Lecteur",
                        )
                        midi_output = gr.File(label="Télécharger MIDI")
                        abc_output = gr.Textbox(
                            label="Notation ABC",
                            lines=10,
                            max_lines=18,
                            elem_classes=["abc-mono"],
                        )

                gr.Examples(
                    label="Exemples",
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
                    outputs=[abc_output, midi_output, midi_player, midi_status],
                )

    return demo, theme, CUSTOM_CSS


if __name__ == "__main__":
    interface_config = config.get("interface", {})
    default_port = interface_config.get("server_port", 7860)
    port = find_free_port(default_port) or default_port

    logger.info("Démarrage de l'interface sur le port %s", port)
    demo, theme, css = build_interface()
    demo.launch(
        share=interface_config.get("share", False),
        server_name=interface_config.get("server_name", "0.0.0.0"),
        server_port=port,
        theme=theme,
        css=css,
        head=HEAD_HTML,
    )
