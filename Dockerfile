FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache --update \
    bash \
    curl \
    gcc \
    g++ \
    libffi-dev \
    musl-dev \
    postgresql-dev \
    && python3 -m ensurepip \
    && pip install --no-cache --upgrade pip setuptools

ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s ~/.local/bin/poetry /usr/local/bin/poetry

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false

COPY poetry.lock pyproject.toml /app/

RUN poetry install --no-dev --no-interaction --no-ansi

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]