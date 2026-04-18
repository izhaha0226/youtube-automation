FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/api/ ./apps/api/
COPY configs/ ./configs/
COPY prompts/ ./prompts/

RUN pip install -e apps/api

RUN mkdir -p /app/data /app/obsidian

ENV DATA_DIR=/app/data
ENV OBSIDIAN_VAULT=/app/obsidian
ENV ENV=production

EXPOSE 8787
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8787} --app-dir /app/apps/api
