#!/usr/bin/env python3
"""
COBOL Action Web Server
Serves COBOL-generated actions via HTTP API (no DOOM input yet)
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from flask import Flask, jsonify, render_template_string, request
import threading
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from build_system.ftp_action_reader import FTPActionReader, COBOLCommandParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state
action_reader = None
action_history = []
max_history = 100


# HTML template for web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>DOOM-COBOL Action Server</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #000;
            color: #0f0;
            margin: 20px;
        }
        h1 { 
            color: #ff0; 
            text-align: center;
            text-shadow: 2px 2px #f00;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .status {
            background: #111;
            border: 2px solid #0f0;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .actions {
            background: #111;
            border: 2px solid #0f0;
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            margin: 10px 0;
        }
        .action-item {
            margin: 5px 0;
            padding: 5px;
            border-bottom: 1px solid #030;
        }
        .action-command {
            color: #0ff;
            font-weight: bold;
        }
        .action-meta {
            color: #888;
            font-size: 0.9em;
        }
        .priority-9 { border-left: 5px solid #f00; }
        .priority-7, .priority-8 { border-left: 5px solid #fa0; }
        .priority-5, .priority-6 { border-left: 5px solid #ff0; }
        .priority-1, .priority-2, .priority-3, .priority-4 { border-left: 5px solid #0f0; }
        .endpoints {
            background: #111;
            border: 2px solid #0f0;
            padding: 15px;
            margin: 10px 0;
        }
        code {
            background: #222;
            padding: 2px 5px;
            border-radius: 3px;
        }
        a { color: #0ff; }
        .refresh-btn {
            background: #0f0;
            color: #000;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-family: inherit;
            font-weight: bold;
            border-radius: 5px;
        }
        .refresh-btn:hover {
            background: #0ff;
        }
    </style>
    <script>
        function refreshActions() {
            fetch('/api/actions/recent')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('action-list');
                    container.innerHTML = '';
                    
                    data.actions.forEach(action => {
                        const div = document.createElement('div');
                        div.className = 'action-item priority-' + (action.priority || 5);
                        
                        const cmdDiv = document.createElement('div');
                        cmdDiv.className = 'action-command';
                        cmdDiv.textContent = action.command;
                        
                        const metaDiv = document.createElement('div');
                        metaDiv.className = 'action-meta';
                        metaDiv.textContent = `Source: ${action.source} | ` +
                            `Time: ${new Date(action.timestamp * 1000).toLocaleTimeString()} | ` +
                            `Priority: ${action.priority || 'N/A'} | ` +
                            `Reason: ${action.reason || 'N/A'}`;
                        
                        div.appendChild(cmdDiv);
                        div.appendChild(metaDiv);
                        container.appendChild(div);
                    });
                    
                    document.getElementById('action-count').textContent = data.total;
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                });
        }
        
        // Auto-refresh every 2 seconds
        setInterval(refreshActions, 2000);
        
        // Initial load
        window.onload = refreshActions;
    </script>
</head>
<body>
    <div class="container">
        <h1>DOOM-COBOL ACTION SERVER</h1>
        
        <div class="status">
            <h2>System Status</h2>
            <p>Actions Received: <span id="action-count">0</span></p>
            <p>Last Update: <span id="last-update">-</span></p>
            <p>FTP Monitor: <span style="color: #0f0;">ACTIVE</span></p>
            <button class="refresh-btn" onclick="refreshActions()">REFRESH NOW</button>
        </div>
        
        <div class="actions">
            <h2>Recent Actions</h2>
            <div id="action-list">
                Loading...
            </div>
        </div>
        
        <div class="endpoints">
            <h2>API Endpoints</h2>
            <ul>
                <li><a href="/api/status">/api/status</a> - System status</li>
                <li><a href="/api/actions/recent">/api/actions/recent</a> - Recent actions (last 20)</li>
                <li><a href="/api/actions/all">/api/actions/all</a> - All actions in history</li>
                <li><a href="/api/actions/latest">/api/actions/latest</a> - Most recent action</li>
                <li><a href="/api/actions/poll">/api/actions/poll</a> - Long-poll for new actions</li>
            </ul>
            
            <h3>Example Usage:</h3>
            <code>curl http://localhost:8080/api/actions/latest</code>
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def index():
    """Web interface"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/status')
def api_status():
    """System status endpoint"""
    return jsonify({
        'status': 'online',
        'action_count': len(action_history),
        'monitor_active': action_reader.running if action_reader else False,
        'timestamp': time.time()
    })


@app.route('/api/actions/recent')
def api_recent_actions():
    """Get recent actions"""
    count = request.args.get('count', 20, type=int)
    recent = action_history[-count:] if len(action_history) > count else action_history
    
    # Reverse so newest is first
    recent = list(reversed(recent))
    
    # Add parsed info
    for action in recent:
        if 'cobol' in action:
            action['priority'] = action['cobol'].get('priority', 5)
            action['reason'] = action['cobol'].get('reason', '')
            
    return jsonify({
        'actions': recent,
        'total': len(action_history),
        'timestamp': time.time()
    })


@app.route('/api/actions/all')
def api_all_actions():
    """Get all actions in history"""
    return jsonify({
        'actions': list(reversed(action_history)),
        'total': len(action_history),
        'timestamp': time.time()
    })


@app.route('/api/actions/latest')
def api_latest_action():
    """Get the most recent action"""
    if action_history:
        return jsonify({
            'action': action_history[-1],
            'timestamp': time.time()
        })
    else:
        return jsonify({
            'action': None,
            'message': 'No actions yet',
            'timestamp': time.time()
        })


@app.route('/api/actions/poll')
def api_poll_actions():
    """Long-poll for new actions"""
    last_count = request.args.get('last_count', 0, type=int)
    timeout = request.args.get('timeout', 30, type=int)
    start_time = time.time()
    
    # Wait for new actions or timeout
    while time.time() - start_time < timeout:
        if len(action_history) > last_count:
            new_actions = action_history[last_count:]
            return jsonify({
                'actions': new_actions,
                'total': len(action_history),
                'timestamp': time.time()
            })
        time.sleep(0.1)
        
    # Timeout - no new actions
    return jsonify({
        'actions': [],
        'total': len(action_history),
        'timestamp': time.time()
    })


def monitor_actions():
    """Background thread to monitor for new actions"""
    global action_history
    
    while True:
        try:
            # Get new commands from FTP reader
            commands = action_reader.get_commands(timeout=0.5)
            
            for cmd in commands:
                # Add to history
                action_history.append(cmd)
                
                # Trim history if too long
                if len(action_history) > max_history:
                    action_history = action_history[-max_history:]
                    
                logger.info(f"New action: {cmd['command']}")
                
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            
        time.sleep(0.1)


def main():
    """Run the web server"""
    global action_reader
    
    import argparse
    
    parser = argparse.ArgumentParser(description='COBOL Action Web Server')
    parser.add_argument('--port', type=int, default=8080, help='Web server port')
    parser.add_argument('--watch', default='mvs_datasets', help='Directory to watch')
    parser.add_argument('--test', action='store_true', help='Add test data')
    
    args = parser.parse_args()
    
    # Start FTP action reader
    action_reader = FTPActionReader(args.watch)
    action_reader.start()
    
    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_actions)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Add test data if requested
    if args.test:
        test_actions = [
            {'source': 'test', 'command': 'MOVE FORWARD 2.0', 'timestamp': time.time() - 10},
            {'source': 'test', 'command': 'TURN RIGHT 45', 'timestamp': time.time() - 8},
            {'source': 'test', 'command': 'SHOOT 3', 'timestamp': time.time() - 6},
            {'source': 'test', 'command': 'MOVE BACK 1.5', 'timestamp': time.time() - 4},
            {'source': 'test', 'command': 'WAIT 1.0', 'timestamp': time.time() - 2},
        ]
        action_history.extend(test_actions)
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║            DOOM-COBOL Action Web Server                  ║
╚══════════════════════════════════════════════════════════╝

Web Interface: http://localhost:{args.port}
API Base: http://localhost:{args.port}/api

Monitoring: {args.watch}
Max History: {max_history} actions

NOTE: This server displays actions but does NOT send them to DOOM yet.
That will be implemented in Step 9.

Press Ctrl+C to stop
""")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=args.port, debug=False)


if __name__ == "__main__":
    main()