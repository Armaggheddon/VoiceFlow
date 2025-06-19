FROM python:3.11-slim
WORKDIR /app

# 1. Install the SHARED library
COPY shared/ /app/shared/
RUN pip install --no-cache-dir /app/shared/

# 2. Install SERVICE-SPECIFIC requirements
RUN pip install --no-cache-dir \
    celery[redis] \
    minio \
    fastapi \
    uvicorn \
    python-multipart \
    pydantic

# 3. Copy the service-specific source code
COPY services/api-gateway/ /app/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]