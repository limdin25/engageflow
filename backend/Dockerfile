FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/London

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Copy only backend dependency files first for better caching
COPY backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Playwright deps (keep as-is since your app expects it)
RUN python -m playwright install --with-deps chromium

# Copy backend code
COPY backend/ /app/

EXPOSE 8000

CMD ["bash", "-lc", "bash scripts/bootstrap_db.sh && uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
