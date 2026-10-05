FROM python:3.12-alpine
WORKDIR /app

# For accurate logging, see https://codemia.io/knowledge-hub/path/what_is_the_use_of_pythonunbuffered_in_docker_file
ENV PYTHONUNBUFFERED=1 

COPY . .

RUN pip install --no-cache-dir uv \
 && uv sync --frozen --no-dev --no-cache \
 && pip uninstall -y uv

# Add python venv to path
ENV PATH="/app/.venv/bin:$PATH" 

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["sh"]