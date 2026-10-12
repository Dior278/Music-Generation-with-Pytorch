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

MODE_AUDIO = "Audio (texte → WAV)"
MODE_MIDI = "MIDI (symbolique LSTM)"


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
    lstm_note = (
        "Poids LSTM détectés."
        if lstm_ready
        else "Poids LSTM absents — entraînez via notebooks/train_lstm_colab.ipynb "
        "puis placez best_model.pth et vocab.json à la racine."
    )

    with gr.Blocks(title="Générateur de musique") as demo:
        gr.Markdown(
            "# Générateur de musique\n"
            "Deux moteurs : **MusicGen** (texte → audio WAV, modèle préentraîné) "
            "et **LSTM** (notation ABC → MIDI, modèle entraîné par vous).\n\n"
            f"*{lstm_note}*"
        )

        with gr.Tabs():
            with gr.Tab(MODE_AUDIO):
                with gr.Row():
                    with gr.Column():
                        prompt = gr.Textbox(
                            label="Description",
                            placeholder="ex. calm piano melody with soft strings",
                            lines=3,
                        )
                        duration = gr.Slider(
                            minimum=config.get("audio.min_duration", 5),
                            maximum=config.get("audio.max_duration", 15),
                            value=config.get("audio.default_duration", 8),
                            step=1,
                            label="Durée (secondes)",
                            info="Sur CPU, 5–10 s reste raisonnable",
                        )
                        audio_seed = gr.Number(
                            label="Seed (optionnel)",
                            value=None,
                            precision=0,
                        )
                        audio_btn = gr.Button("Générer l'audio", variant="primary")
                    with gr.Column():
                        audio_status = gr.Textbox(
                            label="Statut",
                            interactive=False,
                            value="Prêt. Le premier chargement télécharge MusicGen.",
                        )
                        audio_out = gr.Audio(label="Lecture / téléchargement WAV", type="filepath")

                gr.Examples(
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

            with gr.Tab(MODE_MIDI):
                with gr.Row():
                    with gr.Column():
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
                            label="Amorce ABC (optionnel)",
                            placeholder="Laisser vide pour une génération automatique",
                            lines=4,
                        )
                        midi_btn = gr.Button("Générer MIDI", variant="primary")
                    with gr.Column():
                        midi_status = gr.Textbox(
                            label="Statut",
                            interactive=False,
                            value="Prêt." if lstm_ready else lstm_note,
                        )
                        abc_output = gr.Textbox(label="Notation ABC", lines=18, max_lines=30)
                        midi_output = gr.File(label="Fichier MIDI")

                gr.Examples(
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
