FROM python:3.11-slim
WORKDIR /app

# 1. Install the SHARED library
COPY shared/ /app/shared/
RUN pip install --no-cache-dir /app/shared/

# Copy and install the requirements
RUN pip install --no-cache-dir \
    gradio \
    httpx \
    pydantic \
    numpy \
    openai

# Copy the application code
COPY services/demo-ui/ /app/

# The command to run the enhanced Gradio application
CMD ["python", "main.py"]