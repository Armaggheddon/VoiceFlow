FROM nvcr.io/nvidia/tritonserver:25.05-py3

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

RUN pip3 install --no-cache-dir \
    openai-whisper \
    chatterbox-tts \
    numpy \
    ffmpeg-python \
    huggingface-hub


# COPY services/inference-service/model_repository /model_repository

CMD ["tritonserver", "--model-repository=/model_repository"]