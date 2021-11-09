FROM python:3.9-slim-buster

RUN pip install --no-cache-dir --upgrade pip

COPY ./Pipfile .
COPY ./Pipfile.lock .

RUN pip install --no-cache-dir pipenv
RUN pipenv install --no-cache-dir --system

COPY ./My24h /app

WORKDIR /app
