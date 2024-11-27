FROM python:3.10-slim

WORKDIR /app

COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y sqlite3 libsqlite3-dev


COPY app/ /app/
WORKDIR /app

CMD ["python", "main.py"]
