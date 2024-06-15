FROM node:lts-slim AS nextjs_builder

WORKDIR /frontend

COPY /frontend/package.json /frontend/pnpm-lock.yaml ./


RUN corepack enable && pnpm install --frozen-lockfile


COPY /frontend .


RUN pnpm run build

# FROM --platform=linux/arm64 python:3-slim-buster


FROM python:3-slim-buster

EXPOSE 8002


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


COPY requirements.txt .
RUN python -m pip install -r requirements.txt


WORKDIR /app


COPY . /app


COPY --from=nextjs_builder /frontend/out /app/frontend/out


RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser


CMD ["gunicorn", "--bind", "0.0.0.0:8002", "jcourses.wsgi"]
