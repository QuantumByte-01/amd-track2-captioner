FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY prompts/ prompts/
COPY run.py .
ARG FIREWORKS_API_KEY=""
ENV FIREWORKS_API_KEY=${FIREWORKS_API_KEY}
ENTRYPOINT ["python", "run.py"]
