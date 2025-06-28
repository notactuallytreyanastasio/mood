FROM python:3.9-slim

# Create working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy FTP server and gateway
COPY mock_ftp_server.py /app/
COPY ftp_gateway.py /app/

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting Mock MVS FTP Server..."\n\
python3 mock_ftp_server.py &\n\
FTP_PID=$!\n\
\n\
echo "Waiting for FTP server to start..."\n\
sleep 2\n\
\n\
echo "Starting FTP Gateway..."\n\
python3 ftp_gateway.py &\n\
GATEWAY_PID=$!\n\
\n\
echo "FTP Gateway ready!"\n\
echo "- FTP Server on port 2121"\n\
echo "- Dataset gateway active"\n\
\n\
# Keep container running\n\
wait $FTP_PID $GATEWAY_PID\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose FTP port
EXPOSE 2121

CMD ["/app/start.sh"]