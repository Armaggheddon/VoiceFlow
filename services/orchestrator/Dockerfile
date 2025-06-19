FROM python:3.11-slim

WORKDIR /app

COPY shared/ /app/shared/
RUN pip install --no-cache-dir /app/shared/

RUN pip install --no-cache-dir \
    celery[redis] \
    redis \
    httpx \
    pydantic

COPY services/orchestrator/ /app/

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]