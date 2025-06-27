FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    libxinerama-dev \
    libxi-dev \
    libxrandr-dev \
    libxcursor-dev \
    libxtst-dev \
    libxkbfile-dev \
    xvfb \
    x11vnc \
    netcat-openbsd \
    procps \
    gdb \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (but will need to run as root for memory access)
RUN useradd -m -s /bin/bash doombridge

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bridge code
COPY doom_bridge.py .
COPY doom_memory.py .
COPY mvs_connector.py .
COPY doom_controller.py .
COPY healthcheck.py .

# Create data directory
RUN mkdir -p /data && chown doombridge:doombridge /data

# Health check script
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python healthcheck.py || exit 1

# Note: Running as root for memory access, but this is contained in Docker
USER root

ENTRYPOINT ["python", "-u"]
CMD ["doom_bridge.py"]