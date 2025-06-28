#!/usr/bin/env python3
"""
Demo of complete DOOM-COBOL loop with simulated game state
"""

import time
import random
import subprocess
import logging
from dataclasses import dataclass
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SimulatedGameState:
    """Simulated DOOM game state"""
    health: int = 100
    armor: int = 50
    ammo: int = 50
    monsters_nearby: int = 0
    
    def update(self, action: str):
        """Update state based on action taken"""
        if "SHOOT" in action:
            self.ammo -= 2
            if self.monsters_nearby > 0:
                self.monsters_nearby -= 1
                
        if "FORWARD" in action:
            # Random encounter
            if random.random() < 0.3:
                self.monsters_nearby += random.randint(1, 3)
                
        # Random damage
        if self.monsters_nearby > 0 and random.random() < 0.5:
            damage = random.randint(5, 15)
            if self.armor > 0:
                self.armor = max(0, self.armor - damage)
            else:
                self.health -= damage
                
    def to_cobol_format(self) -> str:
        """Format as COBOL record"""
        return (f"HEALTH: {self.health:03d}  ARMOR: {self.armor:03d}  "
                f"AMMO: {self.ammo:03d}  ENEMIES: {self.monsters_nearby:02d}")


class COBOLAISimulator:
    """Simulates COBOL AI decisions"""
    
    def make_decision(self, state: SimulatedGameState) -> List[str]:
        """Make tactical decision based on game state"""
        commands = []
        
        # Priority 1: Survival
        if state.health < 30:
            logger.info("🚨 COBOL AI: SURVIVAL MODE - Low health!")
            commands.extend([
                "MOVE BACK 1",
                "TURN LEFT 90",
                "MOVE FORWARD 1"  # Retreat
            ])
            
        # Priority 2: Combat
        elif state.monsters_nearby > 0:
            logger.info(f"⚔️  COBOL AI: COMBAT MODE - {state.monsters_nearby} enemies detected!")
            
            if state.ammo > 10:
                commands.extend([
                    "SHOOT 3",
                    "MOVE LEFT 0.5",  # Strafe
                    "SHOOT 2"
                ])
            else:
                logger.info("📦 COBOL AI: Low ammo - melee tactics")
                commands.append("MOVE FORWARD 0.5")
                
        # Priority 3: Exploration
        else:
            logger.info("🔍 COBOL AI: EXPLORATION MODE")
            commands.extend([
                "MOVE FORWARD 2",
                "TURN RIGHT 45",
                "MOVE FORWARD 1"
            ])
            
        return commands


def send_command(command: str) -> bool:
    """Send command to COBOL interface"""
    try:
        logger.info(f"📤 Sending: {command}")
        result = subprocess.run(
            f'echo "{command}" | nc localhost 9999',
            shell=True,
            capture_output=True,
            text=True,
            timeout=1
        )
        return result.returncode == 0
    except:
        return False


def main():
    print("DOOM-COBOL Full Loop Demo")
    print("=" * 50)
    print("\nThis demonstrates the complete game loop:")
    print("1. Read game state")
    print("2. COBOL AI makes decision")
    print("3. Send commands to DOOM")
    print("4. Update simulated state")
    print("\nMake sure COBOL interface is running!")
    print("./run_local_cobol.sh")
    print()
    
    input("Press Enter to start demo...")
    
    # Initialize
    game_state = SimulatedGameState()
    ai = COBOLAISimulator()
    cycle = 0
    
    try:
        while game_state.health > 0:
            cycle += 1
            print(f"\n{'='*60}")
            print(f"CYCLE {cycle}")
            print(f"{'='*60}")
            
            # Step 1: Display game state (simulating FTP upload to MVS)
            print(f"\n📊 GAME STATE → MVS DATASET 'DOOM.STATE':")
            print(f"   {game_state.to_cobol_format()}")
            
            # Step 2: COBOL AI decision (simulating JCL execution)
            print(f"\n🧮 COBOL PROGRAM 'DOOMAI' EXECUTING...")
            time.sleep(0.5)
            commands = ai.make_decision(game_state)
            
            # Step 3: Execute commands (simulating FTP download and execution)
            print(f"\n🎮 EXECUTING COMMANDS FROM 'DOOM.COMMANDS':")
            for cmd in commands:
                if send_command(cmd):
                    game_state.update(cmd)
                time.sleep(0.5)
                
            # Random events
            if random.random() < 0.2:
                logger.info("💊 Found health pack!")
                game_state.health = min(100, game_state.health + 25)
                
            if random.random() < 0.1:
                logger.info("🔫 Found ammo!")
                game_state.ammo = min(200, game_state.ammo + 50)
                
            # Wait before next cycle
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Demo stopped by user")
        
    print(f"\n💀 GAME OVER - Survived {cycle} cycles!")
    print("\nThis demo showed how:")
    print("• Game state flows from DOOM → FTP → MVS → COBOL")
    print("• COBOL AI analyzes state and makes tactical decisions")
    print("• Commands flow from COBOL → MVS → FTP → DOOM")
    print("• The loop continues until the player dies")


if __name__ == "__main__":
    main()