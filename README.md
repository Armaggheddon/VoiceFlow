# 

<div id="top"></div>
<br/>
<br/>
<br/>


<p align="center">
  <img src=".github/images/voiceflow.png" width="150" alt="VoiceFlow Logo">
</p>
<h1 align="center">
    <a href="https://github.com/Armaggheddon/VoiceFlow">VoiceFlow 🎙️🔊</a>
</h1>

<div align="center">

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](docker-compose.yaml)

**A production-ready microservices platform for AI-powered speech processing**

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [API Reference](#api-reference) • [Client Library](#client-library)

</div>

## Overview

VoiceFlow is a scalable, cloud-native platform that provides two core AI services through a unified API:

- **🎙️ Voice-to-Text (V2T)**: Transcribe audio files to text using Whisper
- **🔊 Text-to-Speech (T2V)**: Convert text to natural-sounding speech

Built with a microservices architecture using FastAPI, Docker, and NVIDIA Triton Inference Server for high-performance AI model serving.

## Features

- 🎙️ **Speech Recognition**: High-accuracy audio transcription using Whisper
- 🔊 **Speech Synthesis**: Natural-sounding text-to-speech conversion
- 🚀 **Microservices Architecture**: Scalable, containerized services
- ⚡ **NVIDIA Triton**: High-performance model inference server
- 📦 **Object Storage**: MinIO for efficient audio file management
- 🔄 **Async Processing**: Celery-based task queue with Redis
- 🎯 **REST API**: Simple, well-documented HTTP endpoints
- 🧹 **Auto Cleanup**: Automatic cleanup of temporary files
- 🎨 **Web Interface**: Built-in Gradio-based demo UI
- 📚 **Python Client**: Feature-rich client library with sync/async support

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM (for AI models)
- NVIDIA GPU (optional, but recommended for better performance)

### 1. Clone and Start

```bash
git clone <repository-url>
cd voiceflow
docker-compose up -d
```

### 2. Verify Services

```bash
# Check all services are running
docker-compose ps

# Test the API
curl http://localhost:8000/health
```

### 3. Access the Demo UI

Open your browser to [http://localhost:7860](http://localhost:7860) to access the web interface.

![Demo UI Screenshot](docs/images/demo-ui-screenshot.png)
*Image: Screenshot of the Gradio demo interface showing transcription and synthesis tabs*

### 4. Try the API

**Transcribe audio:**
```bash
curl -X POST http://localhost:8000/v1/transcribe \
     -F "audio_file=@sample.wav"
```

**Synthesize speech:**
```bash
curl -X POST http://localhost:8000/v1/synthesize \
     -F "text=Hello, this is VoiceFlow!"
```

## Architecture

![System Architecture](docs/images/architecture-diagram.png)
*Image: Microservices architecture diagram showing API Gateway, Orchestrator, STT/TTS services, Triton Server, MinIO, and Redis*

### Core Components

| Service | Technology | Purpose |
|---------|------------|---------|
| **API Gateway** | FastAPI | Public REST API endpoints and file upload handling |
| **Orchestrator** | FastAPI + Celery | Workflow coordination and task management |
| **STT Service** | FastAPI + Triton | Speech-to-text transcription using Whisper |
| **TTS Service** | FastAPI + Triton | Text-to-speech synthesis |
| **Inference Service** | NVIDIA Triton | High-performance model serving |
| **Demo UI** | Gradio | Web-based user interface |
| **Cleanup Worker** | Python + Celery | Automatic file cleanup |

### Infrastructure

- **MinIO**: S3-compatible object storage for audio files
- **Redis**: Message broker and result storage for Celery
- **Docker**: Containerization and orchestration

### Request Flow

#### Voice-to-Text (V2T)
1. Client uploads audio file to API Gateway
2. File stored in MinIO, task queued in Orchestrator
3. STT Service downloads file, processes with Whisper via Triton
4. Transcription result stored in Redis
5. Client polls for result and receives text

#### Text-to-Speech (T2V)
1. Client sends text to API Gateway
2. Task queued in Orchestrator
3. TTS Service generates audio via Triton, uploads to MinIO
4. Audio URL stored in Redis
5. Client polls for result and receives presigned download URL

## Configuration

### Environment Variables

Key configuration options available in `docker-compose.yaml`:

```yaml
# MinIO Configuration
MINIO_ENDPOINT: "minio:9000"
MINIO_ACCESS_KEY: "minioadmin"
MINIO_SECRET_KEY: "minioadmin"

# Redis Configuration  
REDIS_HOST: "redis"
REDIS_PORT: "6379"

# Triton Configuration
TRITON_SERVER_URL: "inference-service:8001"
```

### GPU Support

To enable GPU acceleration:

1. Install NVIDIA Container Toolkit
2. Uncomment GPU sections in `docker-compose.yaml`
3. Restart services:

```bash
docker-compose down
docker-compose up -d
```

### CPU-Only Mode

VoiceFlow works without GPU, though with reduced performance:

```bash
# Use CPU-only configuration
cp docker-compose.cpu.yaml docker-compose.yaml
docker-compose up -d
```

### Custom Models

To use different AI models:

1. Place model files in `services/inference-service/model_repository/`
2. Update model configuration in `config.pbtxt`
3. Rebuild inference service:

```bash
docker-compose build inference-service
docker-compose up -d inference-service
```

### Model Customization

#### STT Models (Whisper)
- **whisper-tiny**: Fastest, lower accuracy (~39MB)
- **whisper-base**: Balanced performance (~74MB) 
- **whisper-small**: Better accuracy (~244MB)
- **whisper-medium**: High accuracy (~769MB)
- **whisper-large**: Best accuracy (~1550MB)

#### TTS Models
- Configure voice models in `services/inference-service/model_repository/tts/`
- Supports various voice styles and languages

## API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### POST /v1/transcribe
Transcribe audio file to text.

**Request:**
```bash
curl -X POST http://localhost:8000/v1/transcribe \
     -F "audio_file=@audio.wav"
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING"
}
```

#### POST /v1/synthesize  
Convert text to speech.

**Request:**
```bash
curl -X POST http://localhost:8000/v1/synthesize \
     -F "text=Hello world"
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001", 
  "status": "PENDING"
}
```

#### GET /v1/tasks/{task_id}
Get task result.

**Transcription Result:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "transcribed_text": "Hello, this is the transcribed text",
  "audio_url": null
}
```

**Synthesis Result:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "SUCCESS", 
  "transcribed_text": null,
  "audio_url": "https://presigned-download-url"
}
```

For complete API documentation, see [SIMPLIFIED_API_DOCUMENTATION.md](SIMPLIFIED_API_DOCUMENTATION.md).

## Client Library

VoiceFlow includes a comprehensive Python client library for easy integration:

### Installation

```bash
cd client-library
pip install -e .
```

### Quick Example

```python
from voiceflow import VoiceFlowClient

# Initialize client
client = VoiceFlowClient(base_url="http://localhost:8000")

# Transcribe audio
result = client.transcribe("audio.wav")
print(f"Transcription: {result.transcribed_text}")

# Synthesize speech
result = client.synthesize("Hello, world!")
print(f"Audio URL: {result.audio_url}")

# Download audio as numpy array
audio_array = client.synthesize("Hello!", output_format="numpy")
```

### Features

- 🔄 **Sync & Async**: Both synchronous and asynchronous interfaces
- 📝 **Type Hints**: Full type annotation support  
- 🛡️ **Error Handling**: Comprehensive error handling
- ⏱️ **Auto Polling**: Built-in result polling with timeouts
- 🎵 **Multiple Formats**: Support for various audio output formats

### Async Usage

```python
import asyncio
from voiceflow import AsyncVoiceFlowClient

async def main():
    async with AsyncVoiceFlowClient(base_url="http://localhost:8000") as client:
        # Concurrent processing
        tasks = [
            client.transcribe("audio1.wav"),
            client.transcribe("audio2.wav"),
            client.synthesize("Text to speech")
        ]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            print(result)

asyncio.run(main())
```

See the [client library documentation](client-library/README.md) for detailed examples and API reference.

## Demo UI

VoiceFlow includes a built-in web interface accessible at [http://localhost:7860](http://localhost:7860).

![Demo UI Features](docs/images/demo-ui-features.png)
*Image: Demo UI showing both transcription and synthesis interfaces with file upload and audio playback*

### Features

- 📁 **File Upload**: Drag-and-drop audio file upload
- 🎙️ **Live Recording**: Record audio directly in browser
- 🔊 **Audio Playback**: Play synthesized audio inline
- 📋 **History**: View previous transcriptions and syntheses
- ⚙️ **Configuration**: Adjust API settings and model parameters

### Custom Configuration

The demo UI can be configured via environment variables:

```bash
# Custom API endpoint
export API_GATEWAY_URL="http://your-voiceflow-instance:8000"

# Custom storage endpoint  
export MINIO_URL="http://your-minio:9000"

# Start demo UI
cd services/demo-ui
python main.py
```

## Development

### Project Structure

```
voiceflow/
├── services/
│   ├── api-gateway/          # REST API endpoints
│   ├── orchestrator/         # Task coordination
│   ├── stt-service/          # Speech-to-text
│   ├── tts-service/          # Text-to-speech
│   ├── inference-service/    # NVIDIA Triton models
│   ├── demo-ui/             # Gradio web interface
│   └── cleanup-worker/      # File cleanup
├── client-library/          # Python client
├── shared/                  # Common models and utilities
├── data/                    # Storage volumes
└── docker-compose.yaml      # Service orchestration
```

### Local Development

1. **Setup development environment:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

2. **Start infrastructure services:**
```bash
docker-compose up -d redis minio inference-service
```

3. **Run individual services locally:**
```bash
# Start API Gateway
cd services/api-gateway
python main.py

# Start Orchestrator
cd services/orchestrator  
celery -A tasks worker --loglevel=info
```

### Testing

```bash
# Run integration tests
python main.py

# Test client library
cd client-library
python -m pytest tests/

# Test specific service
cd services/api-gateway
python -m pytest
```

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Production Deployment

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yaml voiceflow
```

### Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n voiceflow
```

### Monitoring

VoiceFlow includes built-in health checks and monitoring:

```bash
# Service health
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics

# Check service logs
docker-compose logs -f api-gateway
```

## Performance Tuning

### Scaling Guidelines

- **API Gateway**: CPU-bound, scale horizontally
- **STT/TTS Services**: GPU-bound, scale based on GPU availability  
- **Orchestrator**: I/O-bound, scale based on queue depth
- **Triton Server**: Memory-bound, tune model batch sizes

### Resource Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16+ GB |
| **GPU** | None | 8+ GB VRAM |
| **Storage** | 10 GB | 100+ GB SSD |

### Optimization Tips

1. **Enable GPU acceleration** for 5-10x performance improvement
2. **Tune batch sizes** in Triton model configurations
3. **Configure connection pooling** for high-throughput scenarios
4. **Use faster storage** (SSD) for MinIO data volumes
5. **Scale horizontally** by adding more service replicas

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose build --no-cache
```

**Audio processing errors:**
```bash
# Check file format support
ffprobe audio_file.wav

# Convert to supported format
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

**GPU not detected:**
```bash
# Verify NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

**High memory usage:**
```bash
# Monitor resource usage
docker stats

# Adjust model configurations
vim services/inference-service/model_repository/*/config.pbtxt
```

### Getting Help

- 📖 Check the [documentation](docs/)
- 🐛 Report issues on [GitHub Issues](issues)
- 💬 Join our [Discord community](discord-invite-link)
- 📧 Email support: support@voiceflow.dev

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [NVIDIA Triton](https://github.com/triton-inference-server) for model serving
- [FastAPI](https://fastapi.tiangolo.com/) for API framework
- [Gradio](https://gradio.app/) for the demo interface

---

<div align="center">

**Built with ❤️ for the AI community**

[⬆ Back to Top](#voiceflow-️)

</div>