FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    proftpd \
    && rm -rf /var/lib/apt/lists/*

# Simple FTP proxy - for now just skip this service
CMD ["echo", "FTP gateway placeholder"]