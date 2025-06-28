FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install psutil

# Create working directory
WORKDIR /app

# Copy bridge components
COPY *.py /app/

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting DOOM-COBOL Bridge..."\n\
echo "Waiting for services..."\n\
\n\
# Wait for FTP gateway\n\
while ! nc -z ftp-gateway 2121; do\n\
  echo "Waiting for FTP gateway..."\n\
  sleep 1\n\
done\n\
\n\
# Wait for COBOL interface\n\
while ! nc -z cobol-interface 9999; do\n\
  echo "Waiting for COBOL interface..."\n\
  sleep 1\n\
done\n\
\n\
echo "All services ready!"\n\
\n\
# Monitor state file and process\n\
python3 -u - << EOF\n\
import time\n\
import os\n\
import logging\n\
from ftp_gateway import DoomFTPBridge\n\
\n\
logging.basicConfig(level=logging.INFO)\n\
logger = logging.getLogger(__name__)\n\
\n\
# Override FTP host\n\
bridge = DoomFTPBridge()\n\
bridge.mvs.host = "ftp-gateway"\n\
bridge.mvs.port = 2121\n\
\n\
logger.info("Starting bridge with FTP host: ftp-gateway:2121")\n\
\n\
if bridge.start():\n\
    logger.info("Bridge started successfully")\n\
    try:\n\
        while True:\n\
            time.sleep(1)\n\
    except KeyboardInterrupt:\n\
        bridge.stop()\n\
else:\n\
    logger.error("Failed to start bridge")\n\
EOF\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]