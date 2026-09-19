FROM python:3.12-alpine
WORKDIR /app

COPY . .

RUN pip install --no-cache-dir uv \
 && uv sync --frozen --no-dev --no-cache \
 && pip uninstall -y uv

ENV PATH="/app/.venv/bin:$PATH"

CMD ["gunicorn", "-b", "0.0.0.0:8080", "src.app:app"]