"""
Asynchronous VoiceFlow client.
"""

import asyncio
from pathlib import Path
from typing import Union, Optional

import httpx
import numpy as np

from .models import (
    TranscriptionResult,
    SynthesisResult,
    TaskStatus,
    VoiceFlowError,
    TaskTimeoutError,
    APIError,
    AudioOutputFormat
)
from .utils import (
    extract_filename_from_url,
    download_audio_as_bytes_async,
    audio_bytes_to_numpy,
    save_audio_bytes_to_file
)


class AsyncVoiceFlowClient:
    """Asynchronous client for VoiceFlow API."""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        poll_interval: float = 2.0
    ):
        """
        Initialize the async VoiceFlow client.
        
        Args:
            base_url: Base URL of the VoiceFlow API
            timeout: Request timeout in seconds
            poll_interval: Polling interval for task results in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the client."""
        await self._client.aclose()
    
    async def health_check(self) -> bool:
        """
        Check if the API is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._client.get(f"{self.base_url}/health")
            response.raise_for_status()
            result = response.json()
            return result.get("status") == "ok"
        except Exception:
            return False
    
    async def transcribe(
        self, 
        audio_file: Union[str, Path, bytes],
        filename: Optional[str] = None,
        poll_timeout: float = 120.0
    ) -> TranscriptionResult:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_file: Path to audio file, or audio bytes
            filename: Filename to use when uploading bytes
            poll_timeout: Maximum time to wait for transcription completion
            
        Returns:
            TranscriptionResult with transcribed text
            
        Raises:
            VoiceFlowError: If transcription fails
            TaskTimeoutError: If task times out
        """
        # Submit transcription task
        task_id = await self._submit_transcription(audio_file, filename)
        
        # Poll for result
        return await self._poll_transcription_result(task_id, poll_timeout)
    
    async def synthesize(
        self, 
        text: str,
        output_format: AudioOutputFormat = AudioOutputFormat.URL,
        save_path: Optional[Union[str, Path]] = None,
        poll_timeout: float = 120.0
    ) -> SynthesisResult:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            output_format: Format for audio output (URL, numpy array, or file)
            save_path: Path to save audio file (only used when output_format is FILE)
            poll_timeout: Maximum time to wait for synthesis completion
            
        Returns:
            SynthesisResult with audio in the requested format
            
        Raises:
            VoiceFlowError: If synthesis fails
            TaskTimeoutError: If task times out
        """
        if not text.strip():
            raise VoiceFlowError("Text cannot be empty")
        
        # Submit synthesis task
        task_id = await self._submit_synthesis(text)
        
        # Poll for result
        result = await self._poll_synthesis_result(task_id, poll_timeout)
        
        # Process audio based on output format
        if output_format == AudioOutputFormat.URL:
            return result
        elif output_format == AudioOutputFormat.NUMPY:
            return await self._convert_to_numpy(result)
        elif output_format == AudioOutputFormat.FILE:
            return await self._save_to_file(result, save_path)
        else:
            raise VoiceFlowError(f"Unsupported output format: {output_format}")
    
    async def get_task_result(self, task_id: str) -> Union[TranscriptionResult, SynthesisResult]:
        """
        Get the result of a task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task result
            
        Raises:
            VoiceFlowError: If request fails
        """
        try:
            response = await self._client.get(f"{self.base_url}/v1/tasks/{task_id}")
            response.raise_for_status()
            data = response.json()
            
            status = TaskStatus(data["status"])
            
            # Determine result type based on response content
            if "transcribed_text" in data and data["transcribed_text"] is not None:
                return TranscriptionResult(
                    task_id=task_id,
                    status=status,
                    transcribed_text=data.get("transcribed_text"),
                    error_message=data.get("error_message")
                )
            else:
                # Handle audio URL - prepend base URL if it's a relative path
                audio_url = data.get("audio_url")
                if audio_url and audio_url.startswith("/"):
                    audio_url = f"{self.base_url}{audio_url}"
                
                return SynthesisResult(
                    task_id=task_id,
                    status=status,
                    audio_url=audio_url,
                    error_message=data.get("error_message")
                )
                
        except httpx.HTTPStatusError as e:
            raise APIError(f"HTTP {e.response.status_code}: {e.response.text}", e.response.status_code)
        except Exception as e:
            raise VoiceFlowError(f"Failed to get task result: {e}")
    
    async def _submit_transcription(self, audio_file: Union[str, Path, bytes], filename: Optional[str]) -> str:
        """Submit a transcription task."""
        try:
            if isinstance(audio_file, (str, Path)):
                with open(audio_file, "rb") as f:
                    files = {"audio_file": (Path(audio_file).name, f, "audio/wav")}
                    response = await self._client.post(f"{self.base_url}/v1/transcribe", files=files)
            else:
                # Handle bytes
                fname = filename or "audio.wav"
                files = {"audio_file": (fname, audio_file, "audio/wav")}
                response = await self._client.post(f"{self.base_url}/v1/transcribe", files=files)
            
            response.raise_for_status()
            data = response.json()
            return data["task_id"]
            
        except httpx.HTTPStatusError as e:
            raise APIError(f"HTTP {e.response.status_code}: {e.response.text}", e.response.status_code)
        except Exception as e:
            raise VoiceFlowError(f"Failed to submit transcription: {e}")
    
    async def _submit_synthesis(self, text: str) -> str:
        """Submit a synthesis task."""
        try:
            data = {"text": text}
            response = await self._client.post(f"{self.base_url}/v1/synthesize", data=data)
            response.raise_for_status()
            result = response.json()
            return result["task_id"]
            
        except httpx.HTTPStatusError as e:
            raise APIError(f"HTTP {e.response.status_code}: {e.response.text}", e.response.status_code)
        except Exception as e:
            raise VoiceFlowError(f"Failed to submit synthesis: {e}")
    
    async def _poll_transcription_result(self, task_id: str, timeout: float) -> TranscriptionResult:
        """Poll for transcription result."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            result = await self.get_task_result(task_id)
            
            if result.status == TaskStatus.SUCCESS:
                return result
            elif result.status == TaskStatus.FAILED:
                raise VoiceFlowError(f"Transcription failed: {result.error_message}")
            
            await asyncio.sleep(self.poll_interval)
        
        raise TaskTimeoutError(f"Transcription task {task_id} timed out after {timeout} seconds")
    
    async def _poll_synthesis_result(self, task_id: str, timeout: float) -> SynthesisResult:
        """Poll for synthesis result."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            result = await self.get_task_result(task_id)
            
            if result.status == TaskStatus.SUCCESS:
                return result
            elif result.status == TaskStatus.FAILED:
                raise VoiceFlowError(f"Synthesis failed: {result.error_message}")
            
            await asyncio.sleep(self.poll_interval)
        
        raise TaskTimeoutError(f"Synthesis task {task_id} timed out after {timeout} seconds")
    
    async def _convert_to_numpy(self, result: SynthesisResult) -> SynthesisResult:
        """Convert synthesis result to numpy array format."""
        if not result.audio_url:
            raise VoiceFlowError("No audio URL available for conversion")
        
        try:
            # Download audio bytes
            audio_bytes = await download_audio_as_bytes_async(result.audio_url, timeout=self.timeout)
            
            # Convert to numpy array
            audio_data = audio_bytes_to_numpy(audio_bytes)
            
            # Return result with numpy data
            return SynthesisResult(
                task_id=result.task_id,
                status=result.status,
                audio_url=result.audio_url,
                audio_data=audio_data,
                error_message=result.error_message
            )
        except Exception as e:
            raise VoiceFlowError(f"Failed to convert audio to numpy array: {e}")
    
    async def _save_to_file(self, result: SynthesisResult, save_path: Optional[Union[str, Path]]) -> SynthesisResult:
        """Save synthesis result to file."""
        if not result.audio_url:
            raise VoiceFlowError("No audio URL available for saving")
        
        try:
            # Download audio bytes
            audio_bytes = await download_audio_as_bytes_async(result.audio_url, timeout=self.timeout)
            
            # Determine save path
            if save_path is None:
                filename = extract_filename_from_url(result.audio_url)
                save_path = Path.cwd() / filename
            else:
                save_path = Path(save_path)
            
            # Save to file
            save_audio_bytes_to_file(audio_bytes, save_path)
            
            # Return result with saved path
            return SynthesisResult(
                task_id=result.task_id,
                status=result.status,
                audio_url=result.audio_url,
                saved_path=save_path,
                error_message=result.error_message
            )
        except Exception as e:
            raise VoiceFlowError(f"Failed to save audio to file: {e}")
