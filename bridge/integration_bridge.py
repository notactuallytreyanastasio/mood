#!/usr/bin/env python3
"""
Complete integration bridge for DOOM-COBOL system
Connects state receiver, AI logic, and command sender
"""

import time
import logging
import threading
import struct
import socket
from typing import Optional
from dataclasses import dataclass
from bridge.state_receiver import DoomStateReceiver, DoomState
from bridge.doom_network_controller import DoomNetworkController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class COBOLAILogic:
    """
    AI logic that mimics COBOL decision making
    """
    
    def __init__(self):
        self.last_health = 100
        self.exploration_angle = 0
        self.combat_cooldown = 0
        
    def make_decision(self, state: DoomState) -> list:
        """Make tactical decision based on game state"""
        commands = []
        
        # Update tracking
        health_delta = state.health - self.last_health
        self.last_health = state.health
        
        # Priority 1: Critical survival
        if state.health < 20:
            logger.warning(f"CRITICAL: Health at {state.health}%!")
            commands.extend([
                ("MOVE", "BACK", 2.0),
                ("TURN", "LEFT", 180),
                ("MOVE", "FORWARD", 1.0)
            ])
            
        # Priority 2: Survival mode
        elif state.health < 40:
            logger.info(f"SURVIVAL: Health at {state.health}%, retreating")
            if health_delta < 0:  # Taking damage
                commands.extend([
                    ("MOVE", "BACK", 1.0),
                    ("TURN", "RIGHT", 90),
                    ("MOVE", "LEFT", 0.5)
                ])
            else:
                commands.append(("MOVE", "BACK", 0.5))
                
        # Priority 3: Combat mode
        elif state.enemy_count > 0 and self.combat_cooldown <= 0:
            logger.info(f"COMBAT: {state.enemy_count} enemies detected")
            
            # Find closest enemy
            if state.enemies:
                closest = min(state.enemies, key=lambda e: e['distance'])
                distance = closest['distance'] >> 16  # Convert fixed point
                
                # Aim at enemy
                if distance < 500:
                    commands.extend([
                        ("SHOOT", None, 3),
                        ("MOVE", "LEFT", 0.3),  # Strafe
                        ("SHOOT", None, 2)
                    ])
                else:
                    commands.extend([
                        ("MOVE", "FORWARD", 0.5),
                        ("SHOOT", None, 1)
                    ])
                    
                self.combat_cooldown = 5  # Prevent spam
                
        # Priority 4: Exploration
        else:
            logger.info("EXPLORATION: Searching area")
            commands.extend([
                ("MOVE", "FORWARD", 1.0),
                ("TURN", "RIGHT", self.exploration_angle % 90)
            ])
            self.exploration_angle += 30
            
        # Reduce cooldowns
        if self.combat_cooldown > 0:
            self.combat_cooldown -= 1
            
        return commands


class DoomCOBOLBridge:
    """
    Main bridge connecting all components
    """
    
    def __init__(self):
        self.running = False
        self.state_receiver = DoomStateReceiver()
        self.controller = DoomNetworkController()
        self.ai_logic = COBOLAILogic()
        self.command_queue = []
        self.stats = {
            'states_received': 0,
            'commands_sent': 0,
            'cycles': 0
        }
        
    def start(self):
        """Start the bridge"""
        self.running = True
        
        # Start state receiver
        self.state_receiver.start(callback=self.on_state_received)
        
        # Start command processor
        cmd_thread = threading.Thread(target=self._process_commands, daemon=True)
        cmd_thread.start()
        
        # Start stats reporter
        stats_thread = threading.Thread(target=self._report_stats, daemon=True)
        stats_thread.start()
        
        logger.info("DOOM-COBOL Bridge started")
        logger.info("Waiting for game state...")
        
    def on_state_received(self, state: DoomState):
        """Called when new game state is received"""
        self.stats['states_received'] += 1
        
        # Make AI decision
        commands = self.ai_logic.make_decision(state)
        
        # Queue commands
        for cmd in commands:
            self.command_queue.append(cmd)
            
    def _process_commands(self):
        """Process queued commands"""
        while self.running:
            if self.command_queue:
                cmd = self.command_queue.pop(0)
                action, param1, param2 = cmd
                
                try:
                    if action == "MOVE":
                        self.controller.move(param1, param2)
                    elif action == "TURN":
                        self.controller.turn(param1, param2)
                    elif action == "SHOOT":
                        self.controller.shoot(param2)
                    elif action == "USE":
                        self.controller.use()
                        
                    self.stats['commands_sent'] += 1
                    
                    # Small delay between commands
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"Command failed: {e}")
                    
            else:
                time.sleep(0.01)
                
    def _report_stats(self):
        """Report statistics periodically"""
        while self.running:
            time.sleep(10)
            self.stats['cycles'] += 1
            
            logger.info(
                f"Stats - Cycles: {self.stats['cycles']}, "
                f"States: {self.stats['states_received']}, "
                f"Commands: {self.stats['commands_sent']}"
            )
            
            # Show current state
            state = self.state_receiver.last_state
            if state:
                logger.info(
                    f"Game - Health: {state.health}, "
                    f"Armor: {state.armor}, "
                    f"Level: E{1}M{state.level}, "
                    f"Enemies: {state.enemy_count}"
                )
                
    def stop(self):
        """Stop the bridge"""
        self.running = False
        self.state_receiver.stop()
        self.controller.stop()
        logger.info("Bridge stopped")


def main():
    """Run the integration bridge"""
    print("DOOM-COBOL Integration Bridge")
    print("=" * 50)
    print()
    print("This bridge connects:")
    print("- Modified DOOM (state export on UDP 31337)")
    print("- AI Logic (COBOL-style decision making)")
    print("- Network Controller (commands on UDP 31338)")
    print()
    print("Prerequisites:")
    print("1. Modified DOOM must be running")
    print("2. DOOM must be in gameplay (not menu)")
    print()
    
    input("Press Enter to start bridge...")
    
    bridge = DoomCOBOLBridge()
    bridge.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        bridge.stop()
        
    print("\nBridge terminated")


if __name__ == "__main__":
    main()