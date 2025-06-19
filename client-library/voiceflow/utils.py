"""
Utility functions for the VoiceFlow client library.
"""

import io
import re
from pathlib import Path
from typing import Union, Optional
from urllib.parse import urlparse, parse_qs

import httpx
import numpy as np
import wave


def extract_filename_from_url(audio_url: str) -> str:
    """
    Extract filename from audio URL by splitting between last "/" and first "?".
    
    Args:
        audio_url: The audio URL
        
    Returns:
        Extracted filename with extension
    """
    # Remove query parameters first
    url_without_params = audio_url.split('?')[0]
    
    # Extract filename from the last part of the path
    filename = url_without_params.split('/')[-1]
    
    # Ensure it has a .wav extension if no extension is present
    if '.' not in filename:
        filename += '.wav'
    
    return filename


def download_audio_as_bytes(audio_url: str, timeout: float = 30.0) -> bytes:
    """
    Download audio file as bytes.
    
    Args:
        audio_url: URL to download audio from
        timeout: Request timeout in seconds
        
    Returns:
        Audio file bytes
        
    Raises:
        Exception: If download fails
    """
    with httpx.Client(timeout=timeout) as client:
        response = client.get(audio_url)
        response.raise_for_status()
        return response.content


async def download_audio_as_bytes_async(audio_url: str, timeout: float = 30.0) -> bytes:
    """
    Download audio file as bytes asynchronously.
    
    Args:
        audio_url: URL to download audio from
        timeout: Request timeout in seconds
        
    Returns:
        Audio file bytes
        
    Raises:
        Exception: If download fails
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(audio_url)
        response.raise_for_status()
        return response.content


def audio_bytes_to_numpy(audio_bytes: bytes) -> np.ndarray:
    """
    Convert audio bytes to numpy array.
    
    Args:
        audio_bytes: Audio file bytes (WAV format)
        
    Returns:
        Numpy array containing audio data
        
    Raises:
        Exception: If conversion fails
    """
    # Create a BytesIO object from the audio bytes
    audio_io = io.BytesIO(audio_bytes)
    
    # Open the WAV file
    with wave.open(audio_io, 'rb') as wav_file:
        # Get audio parameters
        frames = wav_file.getnframes()
        sample_width = wav_file.getsampwidth()
        channels = wav_file.getnchannels()
        
        # Read all frames
        raw_audio = wav_file.readframes(frames)
        
        # Convert to numpy array based on sample width
        if sample_width == 1:
            # 8-bit audio (unsigned)
            audio_array = np.frombuffer(raw_audio, dtype=np.uint8)
        elif sample_width == 2:
            # 16-bit audio (signed)
            audio_array = np.frombuffer(raw_audio, dtype=np.int16)
        elif sample_width == 4:
            # 32-bit audio (signed)
            audio_array = np.frombuffer(raw_audio, dtype=np.int32)
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")
        
        # Reshape for stereo audio
        if channels > 1:
            audio_array = audio_array.reshape(-1, channels)
    
    return audio_array


def save_audio_bytes_to_file(audio_bytes: bytes, file_path: Union[str, Path]) -> None:
    """
    Save audio bytes to a file.
    
    Args:
        audio_bytes: Audio file bytes
        file_path: Path where to save the file
        
    Raises:
        Exception: If saving fails
    """
    file_path = Path(file_path)
    
    # Create parent directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the audio bytes to file
    with open(file_path, 'wb') as f:
        f.write(audio_bytes)