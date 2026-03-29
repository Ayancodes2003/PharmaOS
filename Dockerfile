FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY scripts ./scripts
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

RUN pip install --upgrade pip \
    && pip install .

RUN useradd --create-home --shell /bin/bash appuser

RUN mkdir -p /app/artifacts /app/data/raw /app/data/processed /app/data/load_ready /app/data/feature_ready /app/data/feature_store /app/data/analytics_marts

USER appuser

EXPOSE 8000

CMD ["uvicorn", "pharma_os.main:app", "--host", "0.0.0.0", "--port", "8000"]
