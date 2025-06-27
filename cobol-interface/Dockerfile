FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy interface code
COPY cobol_interface.py .
COPY command_parser.py .
COPY jcl_generator.py .

# Create directories
RUN mkdir -p /commands /templates

# Copy JCL templates
COPY templates/*.jcl /templates/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD nc -z localhost 9999 || exit 1

EXPOSE 9999

CMD ["python", "-u", "cobol_interface.py"]