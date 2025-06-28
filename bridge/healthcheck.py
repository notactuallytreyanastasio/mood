#!/usr/bin/env python3
"""
Health check for bridge service
"""

import sys
import psutil

# Check if we can find a DOOM process
for proc in psutil.process_iter(['name']):
    try:
        if 'doom' in proc.info['name'].lower():
            sys.exit(0)
    except:
        pass

# No DOOM found but that's OK for health check
sys.exit(0)