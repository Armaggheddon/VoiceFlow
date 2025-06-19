from fastapi import FastAPI, HTTPException, Depends
import tritonclient.grpc as grpcclient
import numpy as np
from minio import Minio
import os
from contextlib import asynccontextmanager

from shared.models import STTRequest, STTResponse

# Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_BUCKET_UNPROCESSED = os.getenv("MINIO_BUCKET_UNPROCESSED", "unprocessed")
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
    title="STT Service",
    description="Speech-to-text service using Triton Inference Server",
    version="1.0.0",
    lifespan=lifespan
)

def get_minio_client():
    return app.state.minio_client

def get_triton_client():
    return app.state.triton_client

@app.post("/v1/transcribe", response_model=STTResponse)
async def transcribe_audio(
    request: STTRequest,
    minio_client: Minio = Depends(get_minio_client),
    triton_client: grpcclient.InferenceServerClient = Depends(get_triton_client)
):
    """Transcribe audio file to text using Whisper model."""
    try:
        audio_object = minio_client.get_object(
            bucket_name=MINIO_BUCKET_UNPROCESSED,
            object_name=request.input_object_name
        )
        audio_bytes = audio_object.read()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not retrieve file: {str(e)}")
    finally:
        audio_object.close()
        audio_object.release_conn()

    # Prepare audio data for Triton inference
    audio_np = np.frombuffer(audio_bytes, dtype=np.uint8)
    audio_np = np.expand_dims(audio_np, axis=0)  # Add batch dimension
    
    inputs = [grpcclient.InferInput("audio_input", audio_np.shape, "UINT8")]
    inputs[0].set_data_from_numpy(audio_np)
    outputs = [grpcclient.InferRequestedOutput("transcribed_text")]

    try:
        results = triton_client.infer(
            model_name="whisper", 
            inputs=inputs,
            outputs=outputs
        )
        
        output_data = results.as_numpy("transcribed_text")
        
        # Handle different output formats
        if len(output_data) > 0:
            if isinstance(output_data[0], bytes):
                transcription = output_data[0].decode('utf-8')
            elif isinstance(output_data[0], str):
                transcription = output_data[0]
            else:
                transcription = str(output_data[0])
        else:
            transcription = ""
            
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Triton inference failed: {str(e)}")
    
    return STTResponse(text=transcription)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}