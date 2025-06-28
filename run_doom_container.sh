#!/bin/bash
# Run DOOM in a container with memory access

echo "Building DOOM container..."
docker build -f docker/Dockerfile.doom-headless -t doom-cobol .

echo
echo "Starting DOOM container..."
echo "This will run:"
echo "- DOOM in Xvfb (headless)"
echo "- COBOL interface on port 9999"
echo "- Memory reader bridge"
echo "- VNC server on port 5900 (password: doom)"
echo

# Create shared directory for state exchange
mkdir -p shared

docker run -it --rm \
  --name doom-cobol \
  -p 9999:9999 \
  -p 8080:8080 \
  -p 5900:5900 \
  -v $(pwd)/shared:/doom/shared \
  --cap-add=SYS_PTRACE \
  doom-cobol