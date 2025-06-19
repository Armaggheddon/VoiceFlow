from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class JobMode(str, Enum):
    V2T = "v2t"  # Voice to Text
    T2V = "t2v"  # Text to Voice

# Service-to-Service API Models

class STTRequest(BaseModel):
    input_object_name: str

class STTResponse(BaseModel):
    text: str

class LLMMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")

class LLMRequest(BaseModel):
    messages: list[LLMMessage] = Field(..., description="List of messages for the LLM")

class LLMResponse(BaseModel):
    completion: str

class TTSRequest(BaseModel):
    text_to_synthesize: str
    task_id: str

class TTSResponse(BaseModel):
    output_object_name: str

# Client-Facing API Models

class TranscriptionResponse(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the transcription job")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current status of the job")

class SynthesisResponse(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the synthesis job")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current status of the job")

class TaskResultResponse(BaseModel):
    task_id: str
    status: TaskStatus
    transcribed_text: Optional[str] = None  # For V2T mode
    audio_url: Optional[str] = None  # For T2V mode
    error_message: Optional[str] = None