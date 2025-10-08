# syntax=docker/dockerfile:1.4
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VENV_PATH=/opt/venv

WORKDIR /app

RUN python -m venv "${VENV_PATH}" && "${VENV_PATH}/bin/pip" install --upgrade pip

COPY pyproject.toml README.md ./
COPY src ./src

RUN "${VENV_PATH}/bin/pip" install .


FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    GROUP_INVITER_CONFIG=/app/config/config.yaml

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY config ./config

RUN mkdir -p /app/logs \
    && addgroup --system bot \
    && adduser --system --ingroup bot --home /app bot \
    && chown -R bot:bot /app

USER bot

VOLUME ["/app/logs"]

ENTRYPOINT ["start-bot"]
