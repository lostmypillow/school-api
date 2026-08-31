# ==========================================
# Stage 1: Build dependencies
# ==========================================
FROM python:3.13-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --no-dev

# ==========================================
# Stage 2: Runtime image
# ==========================================
FROM gcr.io/distroless/python3-debian13

WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages:/app"

EXPOSE 8080

CMD ["-m", "gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]