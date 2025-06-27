#!/usr/bin/env python3
"""
Web UI for DOOM-COBOL System
Provides monitoring and control interface
"""

from flask import Flask, render_template, request, jsonify
import socket
import ftplib
import os
import time
import json
import threading
from datetime import datetime

app = Flask(__name__)

# Configuration
COBOL_INTERFACE_HOST = 'localhost'
COBOL_INTERFACE_PORT = 9999
MVS_HOST = os.environ.get('MVS_HOST', 'mainframe')
MVS_USER = os.environ.get('MVS_USER', 'HERC01')
MVS_PASS = os.environ.get('MVS_PASS', 'CUL8TR')

# In-memory state cache
state_cache = {
    'game_state': {},
    'last_update': None,
    'command_history': [],
    'system_status': {
        'mainframe': 'unknown',
        'bridge': 'unknown',
        'doom': 'unknown'
    }
}


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


@app.route('/api/status')
def get_status():
    """Get current system status"""
    # Update system status
    check_system_status()
    
    return jsonify({
        'game_state': state_cache['game_state'],
        'last_update': state_cache['last_update'],
        'system_status': state_cache['system_status'],
        'command_count': len(state_cache['command_history'])
    })


@app.route('/api/command', methods=['POST'])
def send_command():
    """Send command to DOOM via COBOL interface"""
    data = request.get_json()
    command = data.get('command', '')
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    try:
        # Send to COBOL interface
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((COBOL_INTERFACE_HOST, COBOL_INTERFACE_PORT))
        sock.send(f"{command}\n".encode('utf-8'))
        
        # Get response
        response = sock.recv(1024).decode('utf-8').strip()
        sock.close()
        
        # Log command
        state_cache['command_history'].append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'response': response
        })
        
        # Keep only last 100 commands
        if len(state_cache['command_history']) > 100:
            state_cache['command_history'] = state_cache['command_history'][-100:]
        
        return jsonify({
            'success': response.startswith('OK'),
            'response': response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history')
def get_history():
    """Get command history"""
    return jsonify({
        'history': state_cache['command_history'][-50:]  # Last 50 commands
    })


@app.route('/api/game-state')
def get_game_state():
    """Get detailed game state from MVS"""
    try:
        ftp = ftplib.FTP(MVS_HOST)
        ftp.login(MVS_USER, MVS_PASS)
        
        # Download game state
        data = []
        ftp.retrbinary('RETR DOOM.STATE', data.append)
        ftp.quit()
        
        if data:
            # Parse EBCDIC record
            record = b''.join(data).decode('cp037').strip()
            
            # Parse based on COBOL layout
            state = {
                'tick': int(record[0:9]),
                'player_x': int(record[9:19]),
                'player_y': int(record[19:29]),
                'player_z': int(record[29:39]),
                'player_angle': int(record[39:43]),
                'health': int(record[43:46]),
                'armor': int(record[46:49]),
                'ammo': [
                    int(record[49:52]),
                    int(record[52:55]),
                    int(record[55:58]),
                    int(record[58:61]),
                    int(record[61:64]),
                    int(record[64:67])
                ],
                'current_weapon': int(record[67:68]),
                'level': int(record[68:70])
            }
            
            # Update cache
            state_cache['game_state'] = state
            state_cache['last_update'] = datetime.now().isoformat()
            
            return jsonify(state)
        else:
            return jsonify({'error': 'No game state available'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def check_system_status():
    """Check status of system components"""
    # Check mainframe
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((MVS_HOST, 3270))
        sock.close()
        state_cache['system_status']['mainframe'] = 'online' if result == 0 else 'offline'
    except:
        state_cache['system_status']['mainframe'] = 'error'
    
    # Check COBOL interface
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((COBOL_INTERFACE_HOST, COBOL_INTERFACE_PORT))
        sock.close()
        state_cache['system_status']['bridge'] = 'online' if result == 0 else 'offline'
    except:
        state_cache['system_status']['bridge'] = 'error'
    
    # Check DOOM (via game state freshness)
    if state_cache['last_update']:
        last_update = datetime.fromisoformat(state_cache['last_update'])
        age = (datetime.now() - last_update).total_seconds()
        state_cache['system_status']['doom'] = 'online' if age < 10 else 'stale'
    else:
        state_cache['system_status']['doom'] = 'unknown'


def background_updater():
    """Background thread to update game state"""
    while True:
        try:
            # Get game state
            with app.test_client() as client:
                client.get('/api/game-state')
        except:
            pass
        
        time.sleep(2)  # Update every 2 seconds


if __name__ == '__main__':
    # Start background updater
    updater = threading.Thread(target=background_updater, daemon=True)
    updater.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=8080, debug=False)