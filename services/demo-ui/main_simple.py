import gradio as gr
import httpx
import time
import os
import tempfile
import numpy as np
from typing import Optional, Tuple

# Configuration
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
TRANSCRIBE_URL = f"{API_GATEWAY_URL}/v1/transcribe"
SYNTHESIZE_URL = f"{API_GATEWAY_URL}/v1/synthesize"
RESULT_URL_TEMPLATE = f"{API_GATEWAY_URL}/v1/tasks/{{task_id}}"

def poll_task_result(task_id: str, timeout: int = 60) -> dict:
    """Poll for task completion."""
    result_url = RESULT_URL_TEMPLATE.format(task_id=task_id)
    start_time = time.time()
    
    with httpx.Client(timeout=30.0) as client:
        while time.time() - start_time < timeout:
            try:
                response = client.get(result_url)
                response.raise_for_status()
                result = response.json()
                
                if result["status"] in ["SUCCESS", "FAILED"]:
                    return result
                    
                time.sleep(2)
            except Exception:
                time.sleep(2)
    
    return {"status": "FAILED", "error_message": "Timeout"}

def transcribe_audio(audio_file) -> str:
    """Transcribe audio file to text."""
    if not audio_file:
        return "Please upload an audio file."
    
    try:
        with httpx.Client(timeout=30.0) as client:
            with open(audio_file, "rb") as f:
                files = {"audio_file": ("audio.wav", f, "audio/wav")}
                response = client.post(TRANSCRIBE_URL, files=files)
                response.raise_for_status()
            
            task_data = response.json()
            result = poll_task_result(task_data["task_id"])
            
            if result["status"] == "SUCCESS":
                return result.get("transcribed_text", "No transcription available")
            else:
                return f"❌ Error: {result.get('error_message', 'Unknown error')}"
                
    except Exception as e:
        return f"❌ Transcription failed: {e}"

def synthesize_text(text: str) -> Optional[Tuple[int, np.ndarray]]:
    """Synthesize text to audio."""
    if not text.strip():
        return None
    
    try:
        with httpx.Client(timeout=30.0) as client:
            data = {"text": text.strip()}
            response = client.post(SYNTHESIZE_URL, data=data)
            response.raise_for_status()
            
            task_data = response.json()
            result = poll_task_result(task_data["task_id"])
            
            if result["status"] == "SUCCESS":
                audio_url = result.get("audio_url")
                if audio_url:
                    # Handle relative URLs from the API gateway
                    # The API gateway now returns relative URLs (without MinIO endpoint)
                    # to provide flexibility in deployment configurations
                    if audio_url.startswith("/"):
                        # Prepend the API gateway base URL to relative URLs
                        full_audio_url = f"{API_GATEWAY_URL}{audio_url}"
                    else:
                        # Use the URL as-is if it's already absolute
                        full_audio_url = audio_url
                    
                    # Download audio
                    audio_response = client.get(full_audio_url)
                    audio_response.raise_for_status()
                    
                    # Convert to numpy array for Gradio
                    audio_data = np.frombuffer(audio_response.content, dtype=np.int16)
                    return 24000, audio_data  # Sample rate, audio data
                    
    except Exception as e:
        print(f"Synthesis error: {e}")
    
    return None

def create_interface():
    """Create the Gradio interface."""
    with gr.Blocks(title="VoiceFlow Demo", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🎙️ VoiceFlow Demo")
        gr.Markdown("Test voice-to-text transcription and text-to-speech synthesis")
        
        with gr.Tab("Voice to Text"):
            with gr.Row():
                audio_input = gr.Audio(
                    sources=["upload", "microphone"],
                    type="filepath",
                    label="Upload or Record Audio"
                )
                transcription_output = gr.Textbox(
                    label="Transcription Result",
                    lines=5,
                    placeholder="Transcribed text will appear here..."
                )
            
            transcribe_btn = gr.Button("Transcribe", variant="primary")
            transcribe_btn.click(
                transcribe_audio,
                inputs=[audio_input],
                outputs=[transcription_output]
            )
        
        with gr.Tab("Text to Speech"):
            with gr.Row():
                text_input = gr.Textbox(
                    label="Text to Synthesize",
                    lines=3,
                    placeholder="Enter text to convert to speech..."
                )
                audio_output = gr.Audio(
                    label="Generated Audio",
                    type="numpy"
                )
            
            synthesize_btn = gr.Button("Synthesize", variant="primary")
            synthesize_btn.click(
                synthesize_text,
                inputs=[text_input],
                outputs=[audio_output]
            )
        
        with gr.Tab("Health Check"):
            health_output = gr.Textbox(label="Health Status")
            
            def check_health():
                try:
                    with httpx.Client(timeout=10.0) as client:
                        response = client.get(f"{API_GATEWAY_URL}/health")
                        response.raise_for_status()
                        return "✅ API Gateway is healthy"
                except Exception as e:
                    return f"❌ Health check failed: {e}"
            
            health_btn = gr.Button("Check Health")
            health_btn.click(check_health, outputs=[health_output])
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
