#!/bin/sh

set -o errexit
set -o nounset

PORT=${BACKEND_PORT:-8000}

if [ ${DEBUG:-False} = "True" ]; then
    args="dev --host 0.0.0.0 --port ${PORT}"
else
    args="run --port ${PORT} --workers ${WORKERS:-1}"
fi

echo $args
fastapi $args src/main.py