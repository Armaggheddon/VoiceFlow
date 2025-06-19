from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from celery import Celery
from celery.result import AsyncResult
from minio import Minio
import uuid
import os
from datetime import timedelta
from contextlib import asynccontextmanager

from shared.models import (
    JobMode, TaskResultResponse, TaskStatus,
    TranscriptionResponse, SynthesisResponse
)

# Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_BUCKET_UNPROCESSED = os.getenv("MINIO_BUCKET_UNPROCESSED", "unprocessed")
MINIO_BUCKET_PROCESSED = os.getenv("MINIO_BUCKET_PROCESSED", "processed")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://redis:6379/0")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MinIO and Celery clients."""
    app.state.minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    
    # Ensure buckets exist
    for bucket in [MINIO_BUCKET_UNPROCESSED, MINIO_BUCKET_PROCESSED]:
        if not app.state.minio_client.bucket_exists(bucket):
            app.state.minio_client.make_bucket(bucket)

    app.state.celery_app = Celery(
        "api_gateway",
        broker=CELERY_BROKER_URL,
        backend=CELERY_BACKEND_URL
    )
    app.state.celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=['json'],
        result_accept_content=['json'],
    )
    
    yield
    
    app.state.minio_client.close()


app = FastAPI(
    title="VoiceFlow API Gateway",
    description="Gateway for AI voice processing pipeline",
    version="1.0.0",
    lifespan=lifespan
)

def get_minio_client():
    return app.state.minio_client

def get_celery_app():
    return app.state.celery_app

@app.post("/v1/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    minio_client: Minio = Depends(get_minio_client),
    celery_app: Celery = Depends(get_celery_app)
):
    """Transcribe audio file to text."""
    task_id = str(uuid.uuid4())
    input_object_name = f"{task_id}_{audio_file.filename}"
    
    try:
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_UNPROCESSED,
            object_name=input_object_name,
            data=audio_file.file,
            length=-1,
            part_size=10*1024*1024,
            content_type=audio_file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")

    celery_app.send_task(
        'tasks.process_pipeline',
        args=[JobMode.V2T.value, {"input_object_name": input_object_name}],
        task_id=task_id
    )

    return TranscriptionResponse(task_id=task_id, status=TaskStatus.PENDING)


@app.post("/v1/synthesize", response_model=SynthesisResponse)
async def synthesize_text(
    text: str = Form(...),
    celery_app: Celery = Depends(get_celery_app)
):
    """Convert text to speech."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text content is required")
    
    task_id = str(uuid.uuid4())
    
    celery_app.send_task(
        'tasks.process_pipeline',
        args=[JobMode.T2V.value, {"text": text.strip()}],
        task_id=task_id
    )

    return SynthesisResponse(task_id=task_id, status=TaskStatus.PENDING)

@app.get("/v1/tasks/{task_id}", response_model=TaskResultResponse)
async def get_task_result(
    task_id: str,
    minio_client: Minio = Depends(get_minio_client),
    celery_app: Celery = Depends(get_celery_app)
):
    """Get task result."""
    task = AsyncResult(task_id, app=celery_app)
    
    if not task.ready():
        return TaskResultResponse(task_id=task_id, status=TaskStatus.PENDING)

    if task.failed():
        error_info = task.info.get('error', 'Task failed') if task.info else 'Task failed'
        return TaskResultResponse(task_id=task_id, status=TaskStatus.FAILED, error_message=str(error_info))

    if not task.successful():
        return TaskResultResponse(task_id=task_id, status=TaskStatus.FAILED, error_message="Task was not successful")

    result = task.get()
    audio_url = None
    transcribed_text = None

    # Handle synthesis result (T2V mode)
    if "output_object_name" in result:
        # generate a minio signed url for the audio file
        signed_url = minio_client.presigned_get_object(
            bucket_name=MINIO_BUCKET_PROCESSED,
            object_name=result["output_object_name"],
            expires=timedelta(minutes=15)  # URL valid for 15 minutes
        )
        audio_url = signed_url.split(MINIO_ENDPOINT, 1)[-1] # Remove endpoint part to get relative URL

    # Handle transcription result (V2T mode)
    if "transcribed_text" in result:
        transcribed_text = result["transcribed_text"]

    return TaskResultResponse(
        task_id=task_id,
        status=TaskStatus.SUCCESS,
        audio_url=audio_url,
        transcribed_text=transcribed_text
    )

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}