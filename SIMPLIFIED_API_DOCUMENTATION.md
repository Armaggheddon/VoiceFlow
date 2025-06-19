# VoiceFlow Simplified API Documentation

## Overview

VoiceFlow has been refactored to provide a simplified service for **transcription** and **speech synthesis** only. The API now supports two core functions:

- **Voice-to-Text (V2T)**: Transcribe audio files to text
- **Text-to-Voice (T2V)**: Convert text to synthesized speech

## API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. Transcribe Audio (V2T)

Convert an audio file to text transcription.

**Endpoint:** `POST /v1/transcribe`

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `audio_file`: Audio file (WAV, MP3, etc.)

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "PENDING"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/v1/transcribe \
     -F "audio_file=@sample.wav"
```

### 2. Synthesize Text (T2V)

Convert text to synthesized speech audio.

**Endpoint:** `POST /v1/synthesize`

**Request:**
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:**
  - `text`: Text to convert to speech

**Response:**
```json
{
  "task_id": "uuid-string", 
  "status": "PENDING"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/v1/synthesize \
     -F "text=Hello, this is a test message"
```

### 3. Get Task Result

Poll for the result of a transcription or synthesis task.

**Endpoint:** `GET /v1/tasks/{task_id}`

**Response for V2T (Transcription):**
```json
{
  "task_id": "uuid-string",
  "status": "SUCCESS",
  "transcribed_text": "This is the transcribed text from the audio file",
  "audio_url": null,
  "error_message": null
}
```

**Response for T2V (Synthesis):**
```json
{
  "task_id": "uuid-string", 
  "status": "SUCCESS",
  "transcribed_text": null,
  "audio_url": "https://presigned-url-to-audio-file",
  "error_message": null
}
```

**Response for Pending Tasks:**
```json
{
  "task_id": "uuid-string",
  "status": "PENDING",
  "transcribed_text": null,
  "audio_url": null,
  "error_message": null
}
```

**Response for Failed Tasks:**
```json
{
  "task_id": "uuid-string",
  "status": "FAILED", 
  "transcribed_text": null,
  "audio_url": null,
  "error_message": "Error description"
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/v1/tasks/your-task-id-here
```

## Task Status

Tasks can have one of three statuses:

- `PENDING`: Task is being processed
- `SUCCESS`: Task completed successfully
- `FAILED`: Task failed (check `error_message` for details)

## Usage Flow

### Voice-to-Text (V2T) Flow

1. **Submit audio file** → `POST /v1/transcribe`
2. **Receive task ID** → `{"task_id": "abc-123", "status": "PENDING"}`
3. **Poll for result** → `GET /v1/tasks/abc-123`
4. **Get transcription** → `{"status": "SUCCESS", "transcribed_text": "..."}`

### Text-to-Voice (T2V) Flow

1. **Submit text** → `POST /v1/synthesize`
2. **Receive task ID** → `{"task_id": "def-456", "status": "PENDING"}`
3. **Poll for result** → `GET /v1/tasks/def-456`
4. **Get audio URL** → `{"status": "SUCCESS", "audio_url": "https://..."}`
5. **Download audio** → Use the presigned URL to download the audio file

## Demo UI

A simple web interface is available at:
```
http://localhost:7860
```

The demo UI provides:
- File upload for audio transcription
- Text input for speech synthesis
- Real-time status updates
- Audio playback for synthesis results

## Architecture Changes

The simplified architecture removes the LLM service and conversation management:

- **API Gateway**: Handles requests and provides simplified endpoints
- **Orchestrator**: Directly coordinates STT and TTS services (no LLM)
- **STT Service**: Transcribes audio using Whisper model via Triton
- **TTS Service**: Synthesizes speech using TTS model via Triton
- **Storage**: MinIO for temporary audio file storage
- **Queue**: Redis for task management

## Error Handling

Common error scenarios:

1. **Missing audio file**: 400 Bad Request
2. **Empty text**: 400 Bad Request  
3. **File upload failure**: 500 Internal Server Error
4. **Service unavailable**: 500 Internal Server Error
5. **Task timeout**: Task status remains PENDING (retry recommended)

## Rate Limiting

No explicit rate limiting is currently implemented. Consider implementing rate limiting for production use.

## Security Notes

- Audio URLs are presigned and expire after 15 minutes
- Temporary files are automatically cleaned up after processing
- No authentication is currently required (add for production)
