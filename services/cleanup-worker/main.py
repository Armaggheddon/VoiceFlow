import time
import os
from minio import Minio
import redis

# Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_BUCKET_UNPROCESSED = os.getenv("MINIO_BUCKET_UNPROCESSED", "unprocessed")
MINIO_BUCKET_PROCESSED = os.getenv("MINIO_BUCKET_PROCESSED", "processed")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def main():
    """Main cleanup worker process."""
    print("Cleanup Worker started...")

    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    listen_for_cleanup_events(redis_client, minio_client)

def listen_for_cleanup_events(redis_client, minio_client):
    """Listen for Redis key expiration events."""
    pubsub = redis_client.pubsub()
    pubsub.subscribe("__keyevent@0__:expired")
    print("Listening for cleanup events...")

    for message in pubsub.listen():
        if message["type"] == "message":
            expired_key = message["data"].decode('utf-8')
            if expired_key.startswith("cleanup:"):
                task_id = expired_key.split(":", 1)[1]
                process_cleanup_task(task_id, redis_client, minio_client)

def process_cleanup_task(task_id, redis_client, minio_client):
    """Process cleanup for a specific task."""
    files_key = f"files:{task_id}"
    files_to_delete = [f.decode('utf-8') for f in redis_client.lrange(files_key, 0, -1)]

    if not files_to_delete:
        return
    
    for object_name in files_to_delete:
        bucket = MINIO_BUCKET_UNPROCESSED if "input" in object_name else MINIO_BUCKET_PROCESSED
        try:
            minio_client.remove_object(bucket, object_name)
            print(f"Deleted {object_name} from {bucket}")
        except Exception as e:
            print(f"Error deleting {object_name}: {e}")
        
    redis_client.delete(files_key)
    print(f"Cleanup completed for task {task_id}")

if __name__ == "__main__":
    time.sleep(10)  # Wait for other services to start
    main()