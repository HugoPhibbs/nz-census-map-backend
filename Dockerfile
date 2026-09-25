FROM python:3.12-alpine
WORKDIR /app

COPY . .

RUN pip install --no-cache-dir uv \
 && uv sync --frozen --no-dev --no-cache \
 && pip uninstall -y uv

ENV PATH="/app/.venv/bin:$PATH"

# For simplicity, and since it works, this image is shared both by the API and MCP servers  
#
# Run locally:
#   API: docker run -p 8080:8080 --env-file .env <image> gunicorn -b 0.0.0.0:8080 src.app:app
#   MCP: docker run -p 8080:8080 --env-file .env <image> uvicorn src.mcp_server:app --host 0.0.0.0 --port 8080
CMD ["sh"]