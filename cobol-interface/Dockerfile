FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    curl \
    python3-tk \
    python3-dev \
    xvfb \
    scrot \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy interface code
COPY cobol_interface.py .
COPY mock_mvs.py .
COPY direct_doom.py .
COPY entrypoint.sh .

# Create directories
RUN mkdir -p /commands /templates

# Copy JCL templates
COPY templates/*.jcl /templates/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD nc -z localhost 9999 || exit 1

EXPOSE 9999

CMD ["/app/entrypoint.sh"]