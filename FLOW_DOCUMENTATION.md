# VoiceFlow Corrected Implementation

## Overview

This document describes the corrected implementation of the VoiceFlow pipeline that properly handles message history and follows the expected conversation flow.

## Corrected Flow

### Input Processing
1. **Voice Input (V2V, V2T modes)**:
   - Voice file is converted to text using STT service
   - Converted text is appended to message history as a user message
   - Message history is sent to LLM service
   - LLM response is appended to message history as assistant message

2. **Text Input (T2V, T2T modes)**:
   - New text message is appended to message history as a user message
   - Message history is sent to LLM service
   - LLM response is appended to message history as assistant message

### Output Processing
1. **Voice Output (V2V, T2V modes)**:
   - LLM response text is converted to voice using TTS service
   - Returns both voice file URL and text response
   - Returns updated message history

2. **Text Output (V2T, T2T modes)**:
   - Returns only text response
   - Returns updated message history

## API Changes

### Job Submission Endpoint: `POST /v1/jobs`

**New Parameters:**
- `message_history` (optional): JSON string containing previous conversation history

**Request Examples:**

#### Voice Input with Message History
```bash
curl -X POST "http://localhost:8000/v1/jobs" \
  -F "mode=v2v" \
  -F "audio_file=@voice_message.wav" \
  -F 'message_history=[{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]'
```

#### Text Input with Message History
```bash
curl -X POST "http://localhost:8000/v1/jobs" \
  -F "mode=t2t" \
  -F "prompt=How are you today?" \
  -F 'message_history=[{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]'
```

### Task Result Endpoint: `GET /v1/tasks/{task_id}`

**New Response Fields:**
- `message_history`: Updated conversation history including the latest exchange

**Response Example:**
```json
{
  "task_id": "uuid-here",
  "status": "SUCCESS",
  "result_text": "I'm doing well, thank you for asking!",
  "result_url": "https://minio-url/voice-response.wav",
  "message_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you today?"},
    {"role": "assistant", "content": "I'm doing well, thank you for asking!"}
  ]
}
```

## Technical Implementation Details

### Orchestrator Changes (`services/orchestrator/tasks.py`)

1. **Message History Management**:
   - Extracts existing message history from input
   - Appends new user messages (voice-converted or text)
   - Sends complete history to LLM service
   - Appends LLM response to history
   - Returns updated history in response

2. **Unified LLM Request Format**:
   - All LLM requests now use the `messages` field consistently
   - Fixed the bug where voice input used incorrect `prompt` field

### API Gateway Changes (`services/api-gateway/main.py`)

1. **Input Handling**:
   - Accepts optional `message_history` parameter
   - Parses and validates JSON message history
   - Passes history to orchestrator

2. **Response Handling**:
   - Returns updated message history from orchestrator
   - Maintains backward compatibility for clients not using history

### Shared Models Changes (`shared/shared/models.py`)

1. **TaskResultResponse**:
   - Added `message_history` field to return updated conversation state

## Conversation Flow Examples

### Example 1: Voice-to-Voice Conversation
1. **First Request**: User sends "Hello" (voice) → System responds "Hi there!" (voice + text)
2. **Second Request**: User sends "How are you?" (voice) + previous history → System responds with voice + text + updated history

### Example 2: Mixed Mode Conversation
1. **Text Request**: User sends "What's the weather?" (text) → System responds with text
2. **Voice Request**: User sends voice message + previous history → System responds with voice + text

### Example 3: Text-to-Voice Conversion
1. **Text Input**: User sends "Please read this aloud" (text)
2. **Voice Output**: System converts response to voice and returns both formats

## Benefits of Corrected Implementation

1. **Conversation Continuity**: Messages maintain context across requests
2. **Consistent API**: All LLM requests use proper message format
3. **Flexible Output**: Supports both voice and text outputs with proper history
4. **Backward Compatibility**: Existing clients continue to work
5. **Proper Error Handling**: Maintains robust error handling throughout pipeline

## Migration Notes

- Existing clients will continue to work without providing message history
- New clients should pass message history for better conversational experience
- All responses now include updated message history for client-side storage
