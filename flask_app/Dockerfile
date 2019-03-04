FROM arm32v7/python:stretch

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN mkdir -p /flask_app
WORKDIR /flask_app