import numpy as np
import triton_python_backend_utils as pb_utils
import whisper
import io
import ffmpeg
import os
from pathlib import Path

class TritonPythonModel:
    """
    Implements the Speech-to-Text logic for Triton using the Whisper model.
    """
    def initialize(self, args):
        """
        Called once when the model is loaded. We load the Whisper model here.
        Using "base" for a good balance of speed and accuracy.
        """

        allowed_model_sizes = ["tiny", "base", "small", "medium", "large", "turbo"]

        model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        if model_size not in allowed_model_sizes:
            raise ValueError(f"Invalid WHISPER_MODEL_SIZE: {model_size}. Must be one of {', '.join(allowed_model_sizes)}")
        
        device_str = args["model_instance_kind"]
        if device_str == "GPU":
            model_instance_device_id = args["model_instance_device_id"]
            device = f"cuda:{model_instance_device_id}"
        elif device_str == "CPU":
            device = "cpu"

        model_cache_dir = Path(args["model_repository"]) / args["model_version"] / "model_cache"

        self.model = whisper.load_model(model_size, device=device, download_root=model_cache_dir)
    
    def _load_audio_from_bytes(self, audio_bytes, sr: int = 16000):
        """
        Custom implementation of load_audio in whisper library
        to avoid having to write the audio file to disk

        See https://github.com/openai/whisper/discussions/380#discussioncomment-3928648
        """
        
        try:
            # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
            # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.    
            out, _ = (
                ffmpeg.input("pipe:", threads=0)
                .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=sr)
                .run(cmd="ffmpeg", capture_stdout=True, capture_stderr=True, input=audio_bytes)
            )
        except ffmpeg.Error as e:
            raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

        return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

    def execute(self, requests):
        """
        This function is called for every inference request.
        """
        responses = []
        for request in requests:
            # Get the raw audio bytes from the input tensor
            audio_tensor = pb_utils.get_input_tensor_by_name(request, "audio_input")
            audio_bytes = audio_tensor.as_numpy().tobytes()
            
            whisper_result = self.model.transcribe(
                self._load_audio_from_bytes(audio_bytes=audio_bytes))

            transcribed_text = whisper_result["text"]
            
            # Create the output tensor with the resulting text
            output_tensor = pb_utils.Tensor(
                "transcribed_text",
                # String tensors must be encoded and wrapped in a NumPy object array
                np.array([transcribed_text.encode('utf-8')], dtype=object)
            )

            # Send the response
            inference_response = pb_utils.InferenceResponse(output_tensors=[output_tensor])
            responses.append(inference_response)

        return responses

    def finalize(self):
        """Called when the model is unloaded."""
        self.model = None
        print("Whisper model finalized.", flush=True)