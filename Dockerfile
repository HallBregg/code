FROM python:3.9

RUN apt-get update && apt-get -y upgrade
WORKDIR /app

COPY ./requirements.txt .
RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

COPY . .
