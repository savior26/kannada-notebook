FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TESSERACT_CMD=/usr/bin/tesseract \
    OCR_LANGUAGE=kan \
    HF_HOME=/home/app/.cache/huggingface

WORKDIR /app

# Tesseract and Kannada trained data support scanned Kannada documents.
# libgomp1 is required by common OpenCV / ML runtime wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
        tesseract-ocr \
        tesseract-ocr-kan \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/uploads /home/app/.cache/huggingface \
    && chown -R appuser:appuser /app/uploads /home/app

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
