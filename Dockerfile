
FROM python:3.10.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    sqlite3 \
    sqlcipher \
    libsqlcipher-dev \
    gpg \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .


EXPOSE 5000


ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Start the app
#CMD ["source","project_venv/bin/activate"]
CMD ["python3", "/app/root/main.py"]
