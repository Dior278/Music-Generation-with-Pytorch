"""
Modern Gradio Interface - AI Music Generator

Modern version with attractive design and custom CSS.

Usage:
    python quick_gradio_demo_modern.py
"""

import sys
import io

# Configure UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import gradio as gr
import logging
import tempfile
from pathlib import Path

# Imports from modular structure
from src.generation.music_generator import MusicGenerator
from src.config import get_config
from src.utils.logger_setup import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Configuration
config = get_config()

# Initialize generator
try:
    generator = MusicGenerator()
    logger.info("Generator initialized successfully")
except Exception as e:
    logger.error(f"Error during initialization: {e}")
    raise


def generate_music_interface(temperature, length, key, meter, seed_text):
    """Generation interface for Gradio."""
    try:
        seed = seed_text.strip() if seed_text and seed_text.strip() else None
        
        abc_text = generator.generate(
            seed=seed,
            temperature=float(temperature),
            length=int(length),
            key=key,
            meter=meter
        )
        
        try:
            from src.utils.midi_converter import abc_to_midi
            
            temp_midi = tempfile.NamedTemporaryFile(delete=False, suffix='.mid')
            temp_midi.close()
            
            if abc_to_midi(abc_text, temp_midi.name):
                message = "Music generated successfully!"
                return abc_text, temp_midi.name, message
            else:
                message = "Music generated but MIDI conversion failed"
                return abc_text, None, message
                
        except Exception as e:
            logger.warning(f"MIDI conversion error: {e}")
            message = f"Music generated but MIDI conversion error: {str(e)}"
            return abc_text, None, message
    
    except Exception as e:
        error_msg = f"Error during generation: {str(e)}"
        logger.error(error_msg)
        return "", None, error_msg


# Modern custom CSS
custom_css = """
/* Modern styles for the interface */
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    color: white;
    text-align: center;
}

.main-header h1 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.main-header p {
    margin: 0.5rem 0 0 0;
    font-size: 1.1rem;
    opacity: 0.9;
}

.param-card {
    background: white;
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.param-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

.result-card {
    background: white;
    border-radius: 15px;
    padding: 1.5rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    min-height: 400px;
}

.generate-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 1rem 2rem !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    transition: all 0.3s !important;
    width: 100% !important;
    margin-top: 1rem !important;
}

.generate-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
}

.generate-btn:active {
    transform: translateY(0) !important;
}

.slider-container {
    margin: 1rem 0;
}

.slider-container label {
    font-weight: 600;
    color: #333;
    margin-bottom: 0.5rem;
    display: block;
}

.info-text {
    font-size: 0.9rem;
    color: #666;
    margin-top: 0.5rem;
    font-style: italic;
}

.status-box {
    background: #f8f9fa;
    border-left: 4px solid #667eea;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1rem;
}

.abc-output {
    font-family: 'Courier New', monospace;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid #e0e0e0;
}

.tips-section {
    background: rgba(255,255,255,0.95);
    border-radius: 15px;
    padding: 1.5rem;
    margin-top: 2rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.tips-section h3 {
    color: #667eea;
    margin-top: 0;
}

.tips-section ul {
    list-style: none;
    padding: 0;
}

.tips-section li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #e0e0e0;
}

.tips-section li:last-child {
    border-bottom: none;
}

.tips-section strong {
    color: #764ba2;
}

/* Animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.result-card {
    animation: fadeIn 0.5s ease-out;
}

/* Responsive */
@media (max-width: 768px) {
    .main-header h1 {
        font-size: 1.8rem;
    }
    
    .param-card, .result-card {
        padding: 1rem;
    }
}
"""


def create_interface():
    """Create the modern Gradio interface."""
    
    with gr.Blocks(
        title="AI Music Generator - Modern Version",
        theme=gr.themes.Soft(primary_hue="purple", secondary_hue="purple"),
        css=custom_css
    ) as demo:
        
        # Modern header
        gr.HTML("""
        <div class="main-header">
            <h1>AI Music Generator</h1>
            <p>Create unique piano music with artificial intelligence</p>
        </div>
        """)
        
        with gr.Row():
            # Left column - Parameters
            with gr.Column(scale=1):
                gr.Markdown("### Generation Parameters", elem_classes=["param-card"])
                
                with gr.Group(elem_classes=["param-card"]):
                    temperature = gr.Slider(
                        minimum=config.get("generation.min_temperature", 0.3),
                        maximum=config.get("generation.max_temperature", 1.5),
                        value=config.get("generation.default_temperature", 0.8),
                        step=0.1,
                        label="Temperature (Creativity)",
                        info="Lower = more predictable, higher = more creative",
                        elem_classes=["slider-container"]
                    )
                    
                    length = gr.Slider(
                        minimum=config.get("generation.min_length", 100),
                        maximum=config.get("generation.max_length", 800),
                        value=config.get("generation.default_length", 400),
                        step=50,
                        label="Length",
                        info="Number of characters to generate",
                        elem_classes=["slider-container"]
                    )
                    
                    key = gr.Dropdown(
                        choices=config.get("generation.available_keys", []),
                        value=config.get("generation.default_key", "C"),
                        label="Key",
                        info="Choose the key of your music"
                    )
                    
                    meter = gr.Dropdown(
                        choices=config.get("generation.available_meters", []),
                        value=config.get("generation.default_meter", "4/4"),
                        label="Time Signature",
                        info="Rhythm of the music"
                    )
                    
                    seed_text = gr.Textbox(
                        label="Custom Seed (Optional)",
                        placeholder="Leave empty for auto-generation\n\nExample:\nX:1\nL:1/8\nM:4/4\nK:C",
                        lines=4,
                        info="Custom starting sequence to guide generation"
                    )
                
                generate_btn = gr.Button(
                    "Generate Music",
                    variant="primary",
                    size="lg",
                    elem_classes=["generate-btn"]
                )
            
            # Right column - Results
            with gr.Column(scale=2):
                gr.Markdown("### Results", elem_classes=["result-card"])
                
                with gr.Group(elem_classes=["result-card"]):
                    status_message = gr.Textbox(
                        label="Status",
                        interactive=False,
                        value="Ready to generate...",
                        elem_classes=["status-box"]
                    )
                    
                    abc_output = gr.Textbox(
                        label="ABC Notation",
                        lines=18,
                        max_lines=30,
                        interactive=True,
                        elem_classes=["abc-output"]
                    )
                    
                    midi_output = gr.File(
                        label="Download MIDI",
                        interactive=False
                    )
        
        # Tips section
        with gr.Group(elem_classes=["tips-section"]):
            gr.Markdown("""
            ### Usage Tips
            
            - **Low temperature (0.5-0.7)**: More coherent and "safe" music
            - **Medium temperature (0.8-1.0)**: Good balance creativity/coherence (recommended)
            - **High temperature (1.1-1.5)**: More experimental, may be chaotic
            
            - **Custom seed**: Provide a starting ABC notation to guide generation
            
            ### About
            
            This generator uses an LSTM network trained on thousands of scores.
            Music is generated in ABC notation then converted to MIDI.
            """)
        
        # Examples
        gr.Markdown("""
        ---
        ### Quick Examples
        
        Click on the examples below to test quickly:
        """)
        
        examples = gr.Examples(
            examples=[
                [0.7, 300, "C", "4/4", ""],
                [0.9, 400, "G", "3/4", ""],
                [1.0, 500, "Am", "4/4", ""],
            ],
            inputs=[temperature, length, key, meter, seed_text],
            label="Example Configurations"
        )
        
        # Connect button
        generate_btn.click(
            fn=generate_music_interface,
            inputs=[temperature, length, key, meter, seed_text],
            outputs=[abc_output, midi_output, status_message]
        )
    
    return demo


if __name__ == "__main__":
    import socket
    
    def find_free_port(start_port=7860, max_attempts=10):
        """Find a free port."""
        for i in range(max_attempts):
            port = start_port + i
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return None
    
    print("Starting modern Gradio interface...")
    print(f"   Device: {generator.device}")
    print(f"   Vocabulary: {generator.vocab_size} characters")
    
    interface_config = config.get("interface", {})
    default_port = interface_config.get("server_port", 7860)
    
    port = find_free_port(default_port)
    if port is None:
        print(f"Warning: No free port found between {default_port} and {default_port + 10}")
        print(f"Info: Using default port: {default_port}")
        port = default_port
    else:
        if port != default_port:
            print(f"Info: Port {default_port} occupied, using port {port}")
    
    demo = create_interface()
    demo.launch(
        share=interface_config.get("share", False),
        server_name=interface_config.get("server_name", "0.0.0.0"),
        server_port=port
    )
