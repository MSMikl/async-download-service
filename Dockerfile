# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt update
RUN apt install zip -y
RUN pip install -r requirements.txt
COPY . .
CMD [ "python3", "server.py"]
