import httpx
import redis
from celery import Celery, shared_task
import os

from shared.models import JobMode, STTRequest, TTSRequest

# Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CLEANUP_TTL_SECONDS = int(os.getenv("CLEANUP_TTL_SECONDS", 3600))

SERVICE_URLS = {
    "stt": "http://stt-service:8000/v1/transcribe",
    "tts": "http://tts-service:8000/v1/synthesize"
}

app = Celery(
    "orchestrator",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    task_serializer="json",
    result_serializer="json",
    accept_content=['json'],
    result_accept_content=['json'],
    task_routes={
        'tasks.process_pipeline': {'queue': 'orchestrator'}
    }
)

def _schedule_cleanup(task_id: str, input_data: dict, result_data: dict):
    """Schedule files for deletion by the cleanup-worker."""
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

        files_to_delete = []
        if "input_object_name" in input_data:
            files_to_delete.append(input_data["input_object_name"])
        if "output_object_name" in result_data:
            files_to_delete.append(result_data["output_object_name"])

        if files_to_delete:
            files_key = f"files:{task_id}"
            cleanup_trigger_key = f"cleanup:{task_id}"
            
            redis_client.rpush(files_key, *files_to_delete)
            redis_client.setex(cleanup_trigger_key, CLEANUP_TTL_SECONDS, "1")

    except Exception as e:
        print(f"WARNING: Failed to schedule cleanup for task {task_id}: {e}")


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_pipeline(self, mode: str, input_data: dict):
    """
    Main Celery task for AI pipeline orchestration.
    Supports V2T (Voice-to-Text) and T2V (Text-to-Voice) modes.
    """
    task_id = self.request.id
    
    with httpx.Client(timeout=120.0) as client:
        try:
            if mode == JobMode.V2T:
                if "input_object_name" not in input_data:
                    raise ValueError("input_object_name is required for V2T mode")
                
                stt_payload = STTRequest(input_object_name=input_data["input_object_name"])
                response = client.post(SERVICE_URLS["stt"], json=stt_payload.dict())
                response.raise_for_status()
                transcribed_text = response.json()["text"]
                
                final_result = {"transcribed_text": transcribed_text}

            elif mode == JobMode.T2V:
                if "text" not in input_data:
                    raise ValueError("text is required for T2V mode")
                
                tts_payload = TTSRequest(text_to_synthesize=input_data["text"], task_id=task_id)
                response = client.post(SERVICE_URLS["tts"], json=tts_payload.dict())
                response.raise_for_status()
                output_object_name = response.json()["output_object_name"]
                
                final_result = {"output_object_name": output_object_name}
            
            else:
                raise ValueError(f"Unsupported mode: {mode}")

            # Schedule cleanup for temporary files
            _schedule_cleanup(task_id, input_data, final_result)
            return final_result

        except httpx.HTTPStatusError as e:
            error_details = e.response.json().get("detail", e.response.text) if e.response else str(e)
            raise self.retry(exc=Exception(f"HTTP Error: {error_details}"))
            
        except Exception as e:
            raise self.retry(exc=e)
