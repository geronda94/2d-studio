FROM python:3.12-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 install -y --no-install-recommends \
    libpq-dev \
    gcc \
    ffmpeg \
    xvfb \
    openbox \
    xdotool \
    wget \
    unzip \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
# Lightweight requirements: Whisper runs as a local service (STT_URL), not in-process.
RUN pip install --no-cache-dir --timeout 120 -r requirements.txt

# Download Chromium + ffmpeg for Playwright (avoids playwright install timeouts)
RUN mkdir -p /root/.cache/ms-playwright/chromium-1105 && \
    wget -q -c "https://playwright.azureedge.net/builds/chromium/1105/chromium-linux.zip" -O /tmp/chromium-linux.zip && \
    unzip -q /tmp/chromium-linux.zip -d /root/.cache/ms-playwright/chromium-1105/ && \
    rm /tmp/chromium-linux.zip && \
    mkdir -p /root/.cache/ms-playwright/ffmpeg-1009 && \
    wget -q -c "https://playwright.azureedge.net/builds/ffmpeg/1009/ffmpeg-linux.zip" -O /tmp/ffmpeg-linux.zip && \
    unzip -q /tmp/ffmpeg-linux.zip -d /root/.cache/ms-playwright/ffmpeg-1009/ && \
    rm /tmp/ffmpeg-linux.zip


# Copy the entire app directory (including scripts and JSON config)
COPY . /app

# We want the python path to include /app so it can resolve `backend.main`
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
