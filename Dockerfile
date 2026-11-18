FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY forecastiq ./forecastiq
COPY artifacts ./artifacts
COPY static ./static
COPY templates ./templates

RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 7860
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 60 app:app"]
