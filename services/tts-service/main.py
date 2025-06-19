from fastapi import FastAPI, HTTPException, Depends
import tritonclient.grpc as grpcclient
import numpy as np
from minio import Minio
import io
import os
from contextlib import asynccontextmanager

from shared.models import TTSRequest, TTSResponse

# Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_BUCKET_PROCESSED = os.getenv("MINIO_BUCKET_PROCESSED", "processed")
TRITON_SERVER_URL = os.getenv("TRITON_SERVER_URL", "inference-service:8002")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Triton and MinIO clients."""
    app.state.triton_client = grpcclient.InferenceServerClient(url=TRITON_SERVER_URL)
    app.state.minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    yield
    app.state.triton_client.close()
    app.state.minio_client.close()

app = FastAPI(
    title="TTS Service",
    description="Text-to-speech service using Triton Inference Server",
    version="1.0.0",
    lifespan=lifespan
)

def get_minio_client():
    return app.state.minio_client

def get_triton_client():
    return app.state.triton_client

@app.post("/v1/synthesize", response_model=TTSResponse)
async def synthesize_speech(
    request: TTSRequest,
    minio_client: Minio = Depends(get_minio_client),
    triton_client: grpcclient.InferenceServerClient = Depends(get_triton_client)
):
    """Synthesize speech from text using Chatterbox model."""
    text_bytes = np.array([request.text_to_synthesize.encode('utf-8')], dtype=object)
    text_bytes = np.expand_dims(text_bytes, axis=0)  # Add batch dimension
    
    inputs = [grpcclient.InferInput("text_input", text_bytes.shape, "BYTES")]
    inputs[0].set_data_from_numpy(text_bytes)

    try:
        results = triton_client.infer(model_name="chatterbox", inputs=inputs)
        raw_audio = results.as_numpy("audio_output")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Triton inference failed: {str(e)}")

    output_object_name = f"{request.task_id}.wav"
    audio_bytes_io = io.BytesIO(raw_audio)

    try:
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_PROCESSED,
            object_name=output_object_name,
            data=audio_bytes_io,
            length=len(raw_audio),
            content_type="audio/wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload audio: {str(e)}")
    
    return TTSResponse(output_object_name=output_object_name)

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}