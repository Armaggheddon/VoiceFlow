import gradio as gr
import httpx
import time
import os
from typing import Optional, List, Dict, Tuple, Any
from openai import OpenAI
import json
import tempfile
import numpy as np
import wave

# Get the API Gateway URL from an environment variable for flexibility
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
TRANSCRIBE_URL = f"{API_GATEWAY_URL}/v1/transcribe"
SYNTHESIZE_URL = f"{API_GATEWAY_URL}/v1/synthesize"
RESULT_URL_TEMPLATE = f"{API_GATEWAY_URL}/v1/tasks/{{task_id}}"

# Default Gemini API configuration
DEFAULT_API_KEY = os.getenv("MODEL_API_KEY", "")
DEFAULT_BASE_URL = os.getenv("MODEL_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")

def create_openai_client(api_key: str, base_url: str) -> Optional[OpenAI]:
    """Create a Gemini client with the provided API key and base URL."""
    if not api_key or not api_key.strip():
        return None
    
    try:
        return OpenAI(
            api_key=api_key.strip(),
            base_url=base_url.strip() if base_url else DEFAULT_BASE_URL,
        )
    except Exception as e:
        print(f"Error creating Gemini client: {e}")
        return None

def call_openai_llm(messages: List[Dict[str, str]], api_key: str, base_url: str, model_name: str) -> str:
    """Call OpenAI LLM with conversation history."""
    openai_client = create_openai_client(api_key, base_url)
    
    if not openai_client:
        return "❌ Model API not configured. Please set your API key in the configuration."
    
    try:
        response = openai_client.chat.completions.create(
            model=model_name or DEFAULT_MODEL_NAME,
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ LLM Error: {str(e)}"

def transcribe_audio(audio_file):
    """Transcribe an audio file to text."""
    if audio_file is None:
        return "Please upload an audio file."
    
    return transcribe_audio_file(audio_file)

def transcribe_audio_file(audio_file_path: str) -> str:
    """Transcribe an audio file and return the text."""
    if not audio_file_path:
        return "No audio file provided."
    
    try:
        with open(audio_file_path, "rb") as f:
            files = {"audio_file": ("audio.wav", f, "audio/wav")}
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(TRANSCRIBE_URL, files=files)
                response.raise_for_status()
                
                task_data = response.json()
                task_id = task_data["task_id"]
                
                # Poll for results
                result_url = RESULT_URL_TEMPLATE.format(task_id=task_id)
                
                max_attempts = 60
                for attempt in range(max_attempts):
                    try:
                        result_response = client.get(result_url)
                        result_response.raise_for_status()
                        result = result_response.json()
                        
                        if result["status"] == "SUCCESS":
                            return result.get("transcribed_text", "No transcription available")
                        elif result["status"] == "FAILED":
                            return f"❌ Transcription failed: {result.get('error_message', 'Unknown error')}"
                        
                        time.sleep(2)
                        
                    except httpx.RequestError:
                        time.sleep(2)
                
                return "❌ Transcription timed out"
                
    except Exception as e:
        return f"❌ Transcription error: {e}"

def synthesize_text_to_audio(text: str) -> Optional[str]:
    """Synthesize text to audio and return the file path."""
    if not text or not text.strip():
        return None
    
    try:
        with httpx.Client(timeout=30.0) as client:
            data = {"text": text.strip()}
            response = client.post(SYNTHESIZE_URL, data=data)
            response.raise_for_status()
            
            task_data = response.json()
            task_id = task_data["task_id"]
            
            result_url = RESULT_URL_TEMPLATE.format(task_id=task_id)
            
            max_attempts = 60
            for attempt in range(max_attempts):
                try:
                    result_response = client.get(result_url)
                    result_response.raise_for_status()
                    result = result_response.json()
                    
                    if result["status"] == "SUCCESS":
                        audio_url = result.get("audio_url")
                        if audio_url:
                            # Handle relative URLs from the API gateway
                            # The API gateway now returns relative URLs (without MinIO endpoint)
                            # to provide flexibility in deployment configurations
                            if audio_url.startswith("/"):
                                # Prepend the API gateway base URL to relative URLs
                                full_audio_url = f"{MINIO_URL}{audio_url}"
                            else:
                                # Use the URL as-is if it's already absolute
                                full_audio_url = audio_url
                            
                            # Download the audio file
                            audio_response = client.get(full_audio_url)
                            audio_response.raise_for_status()
                            raw_audio_bytes = np.frombuffer(audio_response.content, dtype=np.int16)
                            # Chatterbox-TTS generates audio at 24000 Hz and 16-bit
                            return 24000, raw_audio_bytes  # Return sample rate and audio data
                        return None
                    elif result["status"] == "FAILED":
                        return None
                    
                    time.sleep(2)
                    
                except httpx.RequestError:
                    time.sleep(2)
            
            return None
            
    except Exception as e:
        print(f"Synthesis error: {e}")
        return None


def chat_error_message(error_message: str, history: List) -> Tuple[List, Dict]:
    error_msg = f"❌ {error_message}"
    history.append({"role": "assistant", "content": error_msg})
    return history, {}

def chat_with_multimodal_input(
    message: Dict[str, Any], 
    history: List, 
    api_key: str, 
    base_url: str, 
    model_name: str,
    enable_tts: bool
) -> Tuple[List, str]:
    """Process multimodal input (text + optional audio) and return chat history using ChatMessage format."""
    
    if not api_key or not api_key.strip():
        error_msg = "❌ Please configure your Model API key first."
        return chat_error_message(error_msg, history)
    
    try:

        # Message is either audio or text, if both takes only audio file
        is_audio_message = True if message["files"] else False

        if not is_audio_message and not message["text"]:
            return chat_error_message("❌ Please provide some text or audio input.", history)

        user_content = []
        if is_audio_message:
            # only one file is expected
            audio_file = message["files"][0]
            if not audio_file.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg', '.flac')):
                return chat_error_message("Invalid file type selected.", history)
            audio_data = read_audio_file_as_numpy(audio_file)
            if not audio_data:
                return chat_error_message("Unable to read audio data.", history)
            sample_rate, audio_array = audio_data
            user_content.append(
                {
                    "role": "user",
                    "content": gr.Audio(
                        value=(sample_rate, audio_array),
                        label="🎙️ Voice Message",
                    )
                }
            )
            
            # Transcribe audio for LLM processing
            transcribed = transcribe_audio_file(audio_file)
            if not transcribed.startswith("❌"):
                user_content.append(
                    {"role": "user", "content": transcribed}
                )
            else:
                return chat_error_message(transcribed, history)
        else:
            user_content.append({"role": "user", "content": message["text"]})
        
        # Add the user message to history
        history.extend(user_content)

        llm_history = []
        for msg in history:
            if isinstance(msg["content"], str):
                llm_history.append(
                    {
                        "role": msg["role"],
                        "content": msg["content"]
                    }
                )
        
        # Get LLM response
        llm_response = call_openai_llm(llm_history, api_key, base_url, model_name)
        
        if llm_response.startswith("❌"):
            return chat_error_message(llm_response, history)

        llm_messages = []
        
        if enable_tts:
            audio_data = synthesize_text_to_audio(llm_response)
            if not audio_data:
                return chat_error_message("❌ Failed to synthesize audio response.", history)
            
            sample_rate, audio_array = audio_data
            # Create audio component for assistant response
            llm_messages.append(
                {
                    "role": "assistant",
                    "content": gr.Audio(
                        value=(sample_rate, audio_array),
                        label="🔊 AI Response Audio",
                        interactive=False
                    )
                }
            )
        llm_messages.append({"role": "assistant", "content": llm_response})

        history.extend(llm_messages)
        
        return history, {}
        
    except Exception as e:
        return chat_error_message(f"❌ Chat error: {e}", history)

def synthesize_text(text):
    """Convert text to speech."""
    if not text or not text.strip():
        return "Please enter some text to synthesize.", None
    
    audio_data = synthesize_text_to_audio(text)
    if audio_data:
        sample_rate, audio_array = audio_data
        return "✅ Synthesis completed successfully!", (sample_rate, audio_array)
    else:
        return "❌ Synthesis failed.", None

def clear_chat():
    """Clear the chat history."""
    return []

def read_audio_file_as_numpy(audio_path: str) -> Optional[Tuple[int, np.ndarray]]:
    """Read audio file and return as numpy array with target sample rate."""
    if not audio_path or not os.path.exists(audio_path):
        return None
    
    try:
        with wave.open(audio_path, 'rb') as wav_file:
            # Get audio properties
            frames = wav_file.readframes(-1)
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            
            # Convert to numpy array
            if sample_width == 1:
                dtype = np.uint8
            elif sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            else:
                dtype = np.float32
            
            audio_data = np.frombuffer(frames, dtype=dtype)
            
            # Handle stereo to mono conversion
            if channels == 2:
                audio_data = audio_data.reshape(-1, 2)
                audio_data = np.mean(audio_data, axis=1)
            
            # Convert to float32 and normalize
            if dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
                if dtype == np.int16:
                    audio_data /= 32768.0
                elif dtype == np.int32:
                    audio_data /= 2147483648.0
                elif dtype == np.uint8:
                    audio_data = (audio_data - 128) / 128.0
            
            return (sample_rate, audio_data)
            
    except Exception as e:
        print(f"Error reading audio file {audio_path}: {e}")
        return None

# Create the Gradio interface
with gr.Blocks(title="VoiceFlow", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎙️ VoiceFlow
    
    Advanced conversational AI interface with voice capabilities:
    - **Smart Chat**: Send text and audio messages in one interface
    - **Voice Synthesis**: Get audio responses from the AI
    - **Direct Services**: Use transcription and synthesis independently
    """)
    
    with gr.Tab("💬 AI Chat"):
        gr.Markdown("### Chat with AI using text, voice, or both!")
        
        with gr.Row():
            with gr.Column(scale=2):
                # Configuration section
                with gr.Group():
                    gr.Markdown("#### 🔧 Configuration")
                    with gr.Row():
                        api_key_input = gr.Textbox(
                            label="Model API Key",
                            placeholder="Enter your Model API key...",
                            type="password",
                            value=DEFAULT_API_KEY
                        )
                        base_url_input = gr.Textbox(
                            label="Base URL",
                            placeholder="Model API base URL",
                            value=DEFAULT_BASE_URL
                        )
                    with gr.Row():
                        model_input = gr.Textbox(
                            label="Model Name",
                            placeholder="e.g., gemini-2.0-flash",
                            value=DEFAULT_MODEL_NAME
                        )
                        enable_tts = gr.Checkbox(
                            label="Enable Text-to-Speech",
                            value=True
                        )
                
                # Chat interface
                chatbot = gr.Chatbot(
                    label="Conversation",
                    show_label=True,
                    # avatar_images=("👤", "🤖"),
                    type="messages"
                )
                
                # Multimodal input
                chat_input = gr.MultimodalTextbox(
                    interactive=True,
                    placeholder="Type a message or record audio...",
                    show_label=False,
                    sources=["microphone"]
                )
                
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary")
        
        # Handle chat interaction
        chat_input.submit(
            fn=chat_with_multimodal_input,
            inputs=[chat_input, chatbot, api_key_input, base_url_input, model_input, enable_tts],
            outputs=[chatbot, chat_input]
        )
        
        clear_btn.click(
            fn=lambda : [],
            outputs=[chatbot]
        )
    
    with gr.Tab("🎙️ Voice-to-Text"):
        gr.Markdown("### Upload an audio file to transcribe it to text")
        
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(
                    label="Upload Audio File",
                    type="filepath",
                    sources=["upload", "microphone"]
                )
                transcribe_btn = gr.Button("Transcribe Audio", variant="primary")
            
            with gr.Column():
                transcription_output = gr.Textbox(
                    label="Transcription Result",
                    placeholder="Transcribed text will appear here...",
                    lines=10,
                    interactive=False
                )
        
        transcribe_btn.click(
            fn=transcribe_audio,
            inputs=[audio_input],
            outputs=[transcription_output]
        )
    
    with gr.Tab("🔊 Text-to-Voice"):
        gr.Markdown("### Enter text to convert it to speech")
        
        with gr.Row():
            with gr.Column():
                text_input_synthesis = gr.Textbox(
                    label="Enter Text to Synthesize",
                    placeholder="Type your text here...",
                    lines=5
                )
                synthesize_btn = gr.Button("Generate Speech", variant="primary")
            
            with gr.Column():
                synthesis_status_direct = gr.Textbox(
                    label="Status",
                    placeholder="Status will appear here...",
                    interactive=False
                )
                audio_output = gr.Audio(
                    label="Generated Audio",
                    interactive=False
                )
        
        synthesize_btn.click(
            fn=synthesize_text,
            inputs=[text_input_synthesis],
            outputs=[synthesis_status_direct, audio_output]
        )
    
    with gr.Tab("ℹ️ Setup & API Information"):
        gr.Markdown(f"""
        ### Environment Setup
        
        Configure your OpenAI API settings in the **AI Chat** tab or set these environment variables:
        
        ```bash
        export MODEL_API_KEY="your-model-api-key"
        export MODEL_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
        export MODEL_NAME="gemini-2.0-flash"
        ```
        
        **Current Status:**
        - VoiceFlow API: `{API_GATEWAY_URL}`
        - Default Gemini API Key: {'✅ Set' if DEFAULT_API_KEY else '❌ Not set'}
        
        ### Features
        
        #### 💬 AI Chat
        - **Multimodal Input**: Send text messages or record audio directly
        - **Voice Responses**: Enable TTS to hear AI responses
        - **Smart Audio Handling**: Automatic transcription of audio inputs
        
        #### 🎙️ Voice-to-Text
        - Upload audio files or record directly
        - Supports multiple audio formats (WAV, MP3, M4A, OGG, FLAC)
        - Get transcriptions
        
        #### 🔊 Text-to-Voice
        - Convert any text to natural speech
        - High-quality audio generation
        - Download generated audio files
        
        ### API Endpoints
        
        **Base URL:** `{API_GATEWAY_URL}`
        """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
