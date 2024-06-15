# Stage 1: Build the Next.js static export
FROM node:lts-slim AS nextjs_builder

# Set working directory
WORKDIR /frontend

# Copy Next.js dependencies
COPY /frontend/package.json /frontend/pnpm-lock.yaml ./

# Enable corepack and install dependencies
RUN corepack enable && pnpm install --frozen-lockfile

# Copy all source files
COPY /frontend .

# Build the Next.js application as a static export
RUN pnpm run export

# Stage 2: Set up the Django application
# FROM --platform=linux/arm64 python:3-slim-buster


FROM python:3-slim-buster
# Expose port for Django
EXPOSE 8002

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy Django requirements and install them
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# Set working directory for Django app
WORKDIR /app

# Copy Django application code
COPY . /app

# Preserve the static export structure from the Next.js build
COPY --from=nextjs_builder /frontend/out /app/frontend/out

# Create a non-root user and adjust permissions
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Default command to run the Django application
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "jcourses.wsgi"]
