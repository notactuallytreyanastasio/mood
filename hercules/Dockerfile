FROM ubuntu:22.04

# Install Hercules and dependencies
RUN apt-get update && apt-get install -y \
    hercules \
    wget \
    unzip \
    x3270 \
    c3270 \
    ftp \
    telnet \
    && rm -rf /var/lib/apt/lists/*

# Create Hercules user
RUN useradd -m -s /bin/bash hercules

# Create directories
RUN mkdir -p /hercules/conf /hercules/dasd /hercules/log /hercules/cckd

# Download TK4- (MVS 3.8j Turnkey System)
# This is a ready-to-run MVS system
WORKDIR /hercules
RUN wget http://wotho.ethz.ch/tk4-/tk4-_v1.00_current.zip \
    && unzip tk4-_v1.00_current.zip \
    && rm tk4-_v1.00_current.zip \
    && mv tk4-* tk4 \
    && chown -R hercules:hercules /hercules

# Copy our custom configuration
COPY hercules.cnf /hercules/conf/
COPY startup.sh /hercules/
RUN chmod +x /hercules/startup.sh

# Expose ports
EXPOSE 3270 8038 3505 3506 2121

# Switch to hercules user
USER hercules
WORKDIR /hercules/tk4

# Start Hercules
CMD ["/hercules/startup.sh"]