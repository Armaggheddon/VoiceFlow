FROM python:3.11-slim
WORKDIR /app

COPY shared/ /app/shared/
RUN pip install --no-cache-dir /app/shared/

RUN pip install --no-cache-dir \
    minio \
    redis \
    pydantic

COPY services/cleanup-worker/ /app/

# The command to run is our main script
CMD ["python", "main.py"]