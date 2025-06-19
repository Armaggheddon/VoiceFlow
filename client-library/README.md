# VoiceFlow Python Client Library

A Python client library for interacting with the VoiceFlow API. Provides both synchronous and asynchronous interfaces for voice-to-text transcription and text-to-speech synthesis.

## Features

- 🎙️ **Voice-to-Text (V2T)**: Transcribe audio files to text
- 🔊 **Text-to-Speech (T2V)**: Convert text to synthesized speech
- 🔄 **Sync & Async**: Both synchronous and asynchronous interfaces
- 📝 **Type Hints**: Full type annotation support
- 🛡️ **Error Handling**: Comprehensive error handling with custom exceptions
- ⏱️ **Automatic Polling**: Built-in task result polling with configurable timeouts

## Installation

```bash
pip install voiceflow-client
```

For development:

```bash
pip install voiceflow-client[dev]
```

## Quick Start

### Synchronous Client

```python
from voiceflow import VoiceFlowClient

# Initialize client
client = VoiceFlowClient(base_url="http://localhost:8000")

# Check health
if client.health_check():
    print("✅ VoiceFlow API is healthy")

# Transcribe audio
result = client.transcribe("path/to/audio.wav")
print(f"Transcription: {result.transcribed_text}")

# Synthesize speech (multiple output formats)
# Option 1: Get URL (default)
result = client.synthesize("Hello, world!")
print(f"Audio URL: {result.audio_url}")

# Option 2: Get as numpy array
from voiceflow import AudioOutputFormat
result = client.synthesize("Hello, world!", output_format=AudioOutputFormat.NUMPY)
print(f"Audio shape: {result.audio_data.shape}")

# Option 3: Save to file
result = client.synthesize("Hello, world!", output_format=AudioOutputFormat.FILE, save_path="output.wav")
print(f"Saved to: {result.saved_path}")

# Close client
client.close()
```

### Asynchronous Client

```python
import asyncio
from voiceflow import AsyncVoiceFlowClient

async def main():
    async with AsyncVoiceFlowClient(base_url="http://localhost:8000") as client:
        # Check health
        is_healthy = await client.health_check()
        print(f"API healthy: {is_healthy}")
        
        # Transcribe audio
        result = await client.transcribe("path/to/audio.wav")
        print(f"Transcription: {result.transcribed_text}")
        
        # Synthesize speech (multiple formats)
        # URL format (default)
        result = await client.synthesize("Hello, world!")
        print(f"Audio URL: {result.audio_url}")
        
        # Numpy format  
        from voiceflow import AudioOutputFormat
        result = await client.synthesize("Hello, world!", output_format=AudioOutputFormat.NUMPY)
        print(f"Audio shape: {result.audio_data.shape}")
        
        # File format
        result = await client.synthesize("Hello, world!", output_format=AudioOutputFormat.FILE, save_path="async_output.wav")
        print(f"Saved to: {result.saved_path}")

asyncio.run(main())
```

### Context Manager Usage

```python
# Synchronous
with VoiceFlowClient() as client:
    result = client.transcribe("audio.wav")
    print(result.transcribed_text)

# Asynchronous
async with AsyncVoiceFlowClient() as client:
    result = await client.transcribe("audio.wav")
    print(result.transcribed_text)
```

## Advanced Usage

### Custom Configuration

```python
client = VoiceFlowClient(
    base_url="https://your-voiceflow-api.com",
    timeout=60.0,          # Request timeout
    poll_interval=1.0      # Task polling interval
)
```

### Working with Audio Bytes

```python
# Upload audio from bytes
with open("audio.wav", "rb") as f:
    audio_bytes = f.read()

result = client.transcribe(audio_bytes, filename="my_audio.wav")
print(result.transcribed_text)
```

### Manual Task Management

```python
# Submit tasks without waiting for completion
client = VoiceFlowClient()

# Submit transcription (returns immediately)
response = client._submit_transcription("audio.wav")
task_id = response  # Get task ID

# Check result later
result = client.get_task_result(task_id)
if result.status == TaskStatus.SUCCESS:
    print(f"Transcription: {result.transcribed_text}")
```

### Error Handling

```python
from voiceflow import VoiceFlowError, TaskTimeoutError, APIError

try:
    result = client.transcribe("audio.wav", poll_timeout=30.0)
    print(result.transcribed_text)
except TaskTimeoutError:
    print("Task timed out")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
except VoiceFlowError as e:
    print(f"VoiceFlow error: {e}")
```

### Synthesis Output Formats

The library supports three different output formats for synthesized audio:

#### 1. URL Format (Default)
```python
# Get audio as downloadable URL (default behavior)
result = client.synthesize("Hello, world!")
print(f"Download URL: {result.audio_url}")

# Or explicitly specify URL format
from voiceflow import AudioOutputFormat
result = client.synthesize("Hello, world!", output_format=AudioOutputFormat.URL)
```

#### 2. Numpy Array Format
```python
# Get audio as numpy array for processing
from voiceflow import AudioOutputFormat
result = client.synthesize("Hello, world!", output_format=AudioOutputFormat.NUMPY)
print(f"Audio data shape: {result.audio_data.shape}")
print(f"Audio data type: {result.audio_data.dtype}")

# Process the audio data
import numpy as np
audio = result.audio_data
normalized_audio = audio / np.max(np.abs(audio))  # Normalize
```

#### 3. File Format
```python
# Save directly to file (auto-generated filename)
from voiceflow import AudioOutputFormat
result = client.synthesize("Hello, world!", output_format=AudioOutputFormat.FILE)
print(f"Audio saved to: {result.saved_path}")

# Save to specific path
result = client.synthesize("Hello, world!", output_format=AudioOutputFormat.FILE, save_path="my_audio.wav")
print(f"Audio saved to: {result.saved_path}")

# The filename is automatically extracted from the URL if not specified
# URL: "http://api.com/audio/uuid-123/generated_audio.wav?download=true"
# Saved as: "generated_audio.wav"
```

#### Using Different Output Formats
```python
from voiceflow import AudioOutputFormat

# URL format (default)
result = client.synthesize("Text")
# or
result = client.synthesize("Text", output_format=AudioOutputFormat.URL)

# Numpy format  
result = client.synthesize("Text", output_format=AudioOutputFormat.NUMPY)

# File format
result = client.synthesize("Text", output_format=AudioOutputFormat.FILE, save_path="output.wav")
```

#### Async Synthesis Formats
```python
# All the same methods work with async client
async with AsyncVoiceFlowClient() as client:
    # URL (default)
    result = await client.synthesize("Hello async world!")
    
    # Numpy
    result = await client.synthesize("Hello async world!", output_format=AudioOutputFormat.NUMPY)
    
    # File
    result = await client.synthesize("Hello async world!", output_format=AudioOutputFormat.FILE, save_path="async_audio.wav")
```

#### Working with SynthesisResult
```python
# SynthesisResult provides convenience methods
result = client.synthesize_as_numpy("Hello, world!")

# Access data using convenience methods
audio_url = result.get_audio_url()        # URL if available
audio_data = result.get_audio_data()      # Numpy array if available  
saved_path = result.get_saved_path()      # File path if saved

# Or access directly
print(f"URL: {result.audio_url}")
print(f"Data shape: {result.audio_data.shape if result.audio_data is not None else None}")
print(f"Saved to: {result.saved_path}")
```

## API Reference

### VoiceFlowClient

#### Methods

- `health_check() -> bool`: Check API health
- `transcribe(audio_file, filename=None, poll_timeout=120.0) -> TranscriptionResult`: Transcribe audio
- `synthesize(text, output_format=AudioOutputFormat.URL, save_path=None, poll_timeout=120.0) -> SynthesisResult`: Synthesize speech with configurable output
- `get_task_result(task_id) -> Union[TranscriptionResult, SynthesisResult]`: Get task result
- `close()`: Close the client

#### Parameters

- `base_url`: API base URL (default: "http://localhost:8000")
- `timeout`: Request timeout in seconds (default: 30.0)
- `poll_interval`: Polling interval in seconds (default: 2.0)

### AsyncVoiceFlowClient

Same interface as `VoiceFlowClient` but all methods are async.

### Result Objects

#### TranscriptionResult

```python
@dataclass
class TranscriptionResult:
    task_id: str
    status: TaskStatus
    transcribed_text: Optional[str] = None
    error_message: Optional[str] = None
```

#### SynthesisResult

```python
@dataclass  
class SynthesisResult:
    task_id: str
    status: TaskStatus
    audio_url: Optional[str] = None
    audio_data: Optional[np.ndarray] = None
    saved_path: Optional[Path] = None
    error_message: Optional[str] = None
    
    # Convenience methods
    def get_audio_url(self) -> Optional[str]
    def get_audio_data(self) -> Optional[np.ndarray]  
    def get_saved_path(self) -> Optional[Path]
```

### Enums

#### AudioOutputFormat
```python
class AudioOutputFormat(str, Enum):
    URL = "url"      # Return audio as downloadable URL
    NUMPY = "numpy"  # Return audio as numpy array
    FILE = "file"    # Save audio to file and return path
```

#### TaskStatus
```python
class TaskStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS" 
    FAILED = "FAILED"
```

### Exceptions

- `VoiceFlowError`: Base exception for all VoiceFlow errors
- `TaskTimeoutError`: Raised when a task times out
- `APIError`: Raised when the API returns an error (includes status_code)

## Examples

See the `examples/` directory for more comprehensive examples:

- `basic_usage.py`: Basic transcription and synthesis with multiple output formats
- `async_usage.py`: Asynchronous client usage with all synthesis formats
- `synthesis_formats_example.py`: Comprehensive demonstration of all synthesis output formats
- `batch_processing.py`: Processing multiple files
- `error_handling.py`: Comprehensive error handling

## Development

### Setup

```bash
git clone https://github.com/voiceflow/voiceflow
cd voiceflow/client-library
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black voiceflow/
isort voiceflow/
```

### Type Checking

```bash
mypy voiceflow/
```

## Requirements

- Python 3.8+
- httpx >= 0.24.0

## License

MIT License. See `LICENSE` file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Support

For issues and questions:

- 📧 Email: support@voiceflow.com
- 🐛 Issues: [GitHub Issues](https://github.com/voiceflow/voiceflow/issues)
- 📖 Documentation: [Full API Documentation](https://docs.voiceflow.com)
