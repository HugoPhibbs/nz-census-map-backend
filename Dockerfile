FROM python:3.12-alpine
WORKDIR /app

COPY . .

# See https://docs.astral.sh/uv/guides/integration/docker/#using-uv-temporarily
# This only installs uv temporarily, saving on image size
RUN --mount=from=ghcr.io/astral-sh/uv:latest,source=/uv,target=/bin/uv \
    uv sync --frozen --no-dev --no-cache

ENV PATH="/app/.venv/bin:$PATH"
CMD ["gunicorn", "-b", "0.0.0.0:8080", "src.app:app"]