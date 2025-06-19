import numpy as np
import triton_python_backend_utils as pb_utils
# --- IMPORTANT: Replace this with your actual TTS library ---
from chatterbox.tts import ChatterboxTTS # This is a placeholder import
import torchaudio as ta
import torch
import io
from huggingface_hub import hf_hub_download
from pathlib import Path

class TritonPythonModel:
    """
    Implements the Text-to-Speech logic for Triton.
    This is a template for integrating a real TTS model.
    """
    def initialize(self, args):
        """
        Called once when the model is loaded. Load the TTS model here.
        """

        device_str = args["model_instance_kind"]
        if device_str == "GPU":
            model_instance_device_id = args["model_instance_device_id"]
            device = f"cuda:{model_instance_device_id}"
        elif device_str == "CPU":
            device = "cpu"
        
        model_cache_dir = Path(args["model_repository"]) / args['model_version'] / "model_cache"
        chatboxtts_files = [
            "ve.safetensors", 
            "t3_cfg.safetensors", 
            "s3gen.safetensors", 
            "tokenizer.json", 
            "conds.pt"
        ]
        # If model is not already downloaded download it
        if not model_cache_dir.exists() or not all((model_cache_dir / file).exists() for file in chatboxtts_files):
            print("Downloading Chatterbox TTS model...")
            for file in chatboxtts_files:
                hf_hub_download(
                    repo_id="ResembleAI/chatterbox",
                    filename=file,
                    local_dir=model_cache_dir,
                    force_download=True
                )
        self.max_length = 200
        self.model = ChatterboxTTS.from_local(model_cache_dir, device=device)
        print("Chatterbox TTS model initialized successfully.")
        print(flush=True)

    def split_text_into_chunks(self, text, max_length):
        """
        Split text into chunks while trying to preserve sentence boundaries.
        """
        text = text.replace('\n', ' ').replace('\r', ' ')
        # Normalize multiple spaces to single spaces
        text = ' '.join(text.split())
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = text.replace('.', '.|').replace('!', '!|').replace('?', '?|').split('|')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed max_length
            if len(current_chunk) + len(sentence) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # If single sentence is too long, split by words
                    words = sentence.split()
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > max_length:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = word
                            else:
                                # If single word is too long, split it
                                chunks.append(word[:max_length])
                                current_chunk = word[max_length:]
                        else:
                            current_chunk += " " + word if current_chunk else word
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def execute(self, requests):
        """
        This function is called for every inference request.
        """
        responses = []
        for request in requests:
            # Get the input text from the input tensor
            text_tensor = pb_utils.get_input_tensor_by_name(request, "text_input")
            # Decode the text from the tensor
            input_text = text_tensor.as_numpy()

            if len(input_text[0]) > 0:
                if isinstance(input_text[0], bytes):
                    input_text = input_text[0].decode('utf-8')
                elif isinstance(input_text[0], str):
                    input_text = input_text[0]
                else:
                    input_text = str(input_text[0])
            else:
                # return error if input text is empty
                raise ValueError("Input text is empty. Please provide valid text for TTS synthesis.")

            # Remove any non utf-8 characters
            input_text = input_text.encode('ascii', 'ignore').decode('utf-8')

            # Split the text into chunks
            text_chunks = self.split_text_into_chunks(input_text, self.max_length)
            audio_chunks = []
            for chunk in text_chunks:
                # Generate audio for each chunk
                generated_voice = self.model.generate(chunk)
                audio_chunks.append(generated_voice)
            
            if len(audio_chunks) == 1:
                final_audio = audio_chunks[0]
            else:
                # Concatenate all audio chunks
                final_audio = torch.cat(audio_chunks, dim=-1)

            wav_audio_bytes = io.BytesIO()
            ta.save(wav_audio_bytes, final_audio, sample_rate=self.model.sr, format="wav")

            # Create the output tensor from the raw audio bytes
            output_tensor = pb_utils.Tensor(
                "audio_output",
                np.frombuffer(wav_audio_bytes.getbuffer(), dtype=np.uint8)
            )

            # Send the response
            inference_response = pb_utils.InferenceResponse(output_tensors=[output_tensor])
            responses.append(inference_response)

        return responses

    def finalize(self):
        """Called when the model is unloaded."""
        self.model = None
        print("Chatterbox TTS model finalized.")