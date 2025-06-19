"""
Data models for the VoiceFlow client library.
"""

from enum import Enum
from typing import Optional, Union
from dataclasses import dataclass
from pathlib import Path

import numpy as np


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class AudioOutputFormat(str, Enum):
    """Audio output format enumeration."""
    URL = "url"
    NUMPY = "numpy"
    FILE = "file"


@dataclass
class TaskResult:
    """Base task result."""
    task_id: str
    status: TaskStatus
    error_message: Optional[str] = None


@dataclass
class TranscriptionResult(TaskResult):
    """Result of a transcription task."""
    transcribed_text: Optional[str] = None


@dataclass
class SynthesisResult(TaskResult):
    """Result of a synthesis task."""
    audio_url: Optional[str] = None
    audio_data: Optional[np.ndarray] = None
    saved_path: Optional[Path] = None
    
    def get_audio_url(self) -> Optional[str]:
        """Get the audio URL."""
        return self.audio_url
    
    def get_audio_data(self) -> Optional[np.ndarray]:
        """Get the audio data as numpy array."""
        return self.audio_data
    
    def get_saved_path(self) -> Optional[Path]:
        """Get the path where audio was saved."""
        return self.saved_path


class VoiceFlowError(Exception):
    """Base exception for VoiceFlow client errors."""
    pass


class TaskTimeoutError(VoiceFlowError):
    """Raised when a task times out."""
    pass


class APIError(VoiceFlowError):
    """Raised when the API returns an error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
