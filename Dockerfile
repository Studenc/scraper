FROM python:latest

WORKDIR /app

COPY requirements.txt .
COPY .env .
COPY main.py .

RUN ls -la

RUN pip install -r requirements.txt
RUN python main.py