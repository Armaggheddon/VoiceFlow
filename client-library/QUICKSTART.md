# VoiceFlow Client Library Quick Setup

## Installation

### From Source (Development)

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd voiceflow/client-library

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e .[dev]
```

### For Distribution

```bash
# Build the package
python -m build

# Install the built package
pip install dist/voiceflow_client-1.0.0-py3-none-any.whl
```

## Quick Test

1. **Start VoiceFlow Services**:
   ```bash
   cd ../  # Go back to main project directory
   docker-compose up -d
   ```

2. **Wait for services to be ready** (about 30-60 seconds)

3. **Run integration test**:
   ```bash
   cd client-library
   python integration_test.py
   ```

4. **Try the examples**:
   ```bash
   python examples/basic_usage.py
   python examples/async_usage.py
   python examples/error_handling.py
   ```

## Usage in Your Code

```python
# Simple usage
from voiceflow import VoiceFlowClient

with VoiceFlowClient() as client:
    # Synthesize speech
    result = client.synthesize("Hello, world!")
    print(f"Audio URL: {result.audio_url}")
    
    # Transcribe audio (if you have an audio file)
    # result = client.transcribe("path/to/audio.wav")
    # print(f"Transcription: {result.transcribed_text}")
```

## Development

```bash
# Run tests
pytest

# Format code
black voiceflow/
isort voiceflow/

# Type checking
mypy voiceflow/
```
