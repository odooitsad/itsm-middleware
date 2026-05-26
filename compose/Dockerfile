FROM python:3.12.13-slim-bookworm

RUN pip install --no-cache-dir poetry==2.3.2

ARG POETRY_ARGS="--no-root"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./compose/start.sh ./

RUN poetry install $POETRY_ARGS && rm -rf $POETRY_CACHE_DIR \
    && chmod +x ./start.sh \
    && mkdir -p ./logs

COPY src ./src

ENTRYPOINT ["./start.sh"]