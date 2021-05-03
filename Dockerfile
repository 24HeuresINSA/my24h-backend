FROM python:3.9

RUN pip install --upgrade pip

COPY ./Pipfile .
COPY ./Pipfile.lock .

RUN pip install pipenv
RUN pipenv install --system

COPY ./My24h /app

WORKDIR /app