FROM python:3.11-slim

WORKDIR /app

COPY shared/ /app/shared/
RUN pip install --no-cache-dir /app/shared

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    tritonclient[all] \
    minio \
    numpy \
    pydantic

COPY services/tts-service/ /app/
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]