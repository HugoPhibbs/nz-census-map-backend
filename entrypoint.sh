#!/bin/sh

# For Posix shells (for Alpine)
case "$1" in
  api) exec gunicorn -b 0.0.0.0:8080 src.app:app ;;
  mcp) exec uvicorn src.mcp_server:app --host 0.0.0.0 --port 8080 ;;
  *)   exec "$@" ;;
esac