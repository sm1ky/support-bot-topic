FROM python:3.12-slim

WORKDIR /usr/src/bot

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.1.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --only main

COPY . .

CMD ["poetry", "run", "python", "-m", "app.bot"]