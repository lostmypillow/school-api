# ==========================================
# Stage 1: Build dependencies
# ==========================================
FROM python:3.13.15-slim-trixie AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --no-dev

# ==========================================
# Stage 2: Runtime image
# ==========================================
FROM python:3.13.15-slim-trixie

WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        unixodbc-dev \
        libgssapi-krb5-2 \
    && DEBIAN_VERSION=$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1) \
    && if ! echo "9 10 11 12 13" | grep -qw "$DEBIAN_VERSION"; then \
        echo "Debian $DEBIAN_VERSION is not currently supported." && exit 1; \
    fi \
    && curl -fsSL -O "https://packages.microsoft.com/config/debian/${DEBIAN_VERSION}/packages-microsoft-prod.deb" \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        mssql-tools18 \
    && echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> /etc/bash.bashrc \
    && rm -rf /var/lib/apt/lists/*


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages:/app"

EXPOSE 8080

CMD ["python", "-m", "gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]