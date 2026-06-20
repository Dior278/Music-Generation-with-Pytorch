"""
Interface web pour le générateur de musique.

Usage:
    python app.py
"""

import logging
import socket
import sys
import tempfile

import gradio as gr

from src.config import get_config
from src.generation.music_generator import MusicGenerator
from src.utils.logger_setup import setup_logging
from src.utils.midi_converter import abc_to_midi

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

setup_logging()
logger = logging.getLogger(__name__)

config = get_config()
generator = MusicGenerator()


def generate_music(temperature, length, key, meter, seed_text):
    """Génère de la musique et retourne le texte ABC, le fichier MIDI et un message."""
    try:
        seed = seed_text.strip() if seed_text and seed_text.strip() else None

        abc_text = generator.generate(
            seed=seed,
            temperature=float(temperature),
            length=int(length),
            key=key,
            meter=meter,
        )

        temp_midi = tempfile.NamedTemporaryFile(delete=False, suffix=".mid")
        temp_midi.close()

        if abc_to_midi(abc_text, temp_midi.name):
            return abc_text, temp_midi.name, "Musique générée avec succès."

        return abc_text, None, "Musique générée, mais la conversion MIDI a échoué."

    except Exception as exc:
        message = f"Erreur lors de la génération : {exc}"
        logger.error(message)
        return "", None, message


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
    with gr.Blocks(title="Générateur de musique") as demo:
        gr.Markdown(
            "# Générateur de musique\n"
            "Composez des morceaux à partir d'un modèle LSTM entraîné sur des partitions ABC."
        )

        with gr.Row():
            with gr.Column():
                temperature = gr.Slider(
                    minimum=config.get("generation.min_temperature", 0.3),
                    maximum=config.get("generation.max_temperature", 1.5),
                    value=config.get("generation.default_temperature", 0.8),
                    step=0.1,
                    label="Température",
                    info="Plus bas = plus prévisible, plus haut = plus créatif",
                )
                length = gr.Slider(
                    minimum=config.get("generation.min_length", 100),
                    maximum=config.get("generation.max_length", 800),
                    value=config.get("generation.default_length", 400),
                    step=50,
                    label="Longueur",
                    info="Nombre de caractères à générer",
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
                generate_btn = gr.Button("Générer", variant="primary")

            with gr.Column():
                status = gr.Textbox(label="Statut", interactive=False, value="Prêt.")
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

        generate_btn.click(
            fn=generate_music,
            inputs=[temperature, length, key, meter, seed_text],
            outputs=[abc_output, midi_output, status],
        )

    return demo


if __name__ == "__main__":
    interface_config = config.get("interface", {})
    default_port = interface_config.get("server_port", 7860)
    port = find_free_port(default_port) or default_port

    logger.info("Démarrage de l'interface sur le port %s", port)
    logger.info("Appareil : %s", generator.device)
    logger.info("Vocabulaire : %s caractères", generator.vocab_size)

    build_interface().launch(
        share=interface_config.get("share", False),
        server_name=interface_config.get("server_name", "0.0.0.0"),
        server_port=port,
    )
