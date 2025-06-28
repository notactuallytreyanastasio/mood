#!/usr/bin/env python3
"""
DOOM State Reader using OCR for macOS
Reads game state from screen instead of memory
"""

import time
import re
from dataclasses import dataclass
from typing import Optional, List
import subprocess
import logging

try:
    from PIL import Image, ImageGrab
    import pytesseract
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/pytesseract not available - OCR disabled")

@dataclass
class DoomState:
    """Current DOOM game state"""
    tick: int
    player_x: int  # These will be estimates
    player_y: int
    player_z: int
    player_angle: int
    health: int
    armor: int
    ammo: List[int]  # [bullets, shells, cells, rockets]
    current_weapon: int
    level: int
    
    def to_cobol_records(self) -> List[str]:
        """Convert to COBOL format records"""
        records = []
        
        # Game state record
        records.append(f"STATE {self.tick:08d} {self.level:02d}")
        
        # Player record
        records.append(f"PLAYER{self.player_x:+08d}{self.player_y:+08d}{self.player_z:+08d}"
                      f"{self.player_angle:+04d}{self.health:03d}{self.armor:03d}")
        
        # Ammo record
        ammo_str = "".join(f"{a:04d}" for a in self.ammo[:4])
        records.append(f"AMMO  {ammo_str}{self.current_weapon:01d}")
        
        return records


class DoomOCRReader:
    """Read DOOM state from screen using OCR"""
    
    def __init__(self):
        self.last_state = None
        self.tick_counter = 0
        
    def capture_doom_window(self) -> Optional[Image.Image]:
        """Capture DOOM window screenshot"""
        if not PIL_AVAILABLE:
            return None
            
        try:
            # Get window bounds using AppleScript
            script = '''
            tell application "System Events"
                tell process "chocolate-doom"
                    get bounds of window 1
                end tell
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                # Parse bounds: "x1, y1, x2, y2"
                bounds = list(map(int, result.stdout.strip().split(', ')))
                # Capture screenshot of DOOM window
                return ImageGrab.grab(bbox=tuple(bounds))
                
        except Exception as e:
            logging.error(f"Failed to capture DOOM window: {e}")
            
        return None
        
    def extract_hud_region(self, screenshot: Image.Image) -> dict:
        """Extract HUD region from screenshot"""
        width, height = screenshot.size
        
        # DOOM HUD is at bottom of screen
        hud_height = int(height * 0.15)  # Bottom 15% of screen
        hud_region = screenshot.crop((0, height - hud_height, width, height))
        
        # Split HUD into sections
        sections = {
            'ammo': hud_region.crop((0, 0, int(width * 0.15), hud_height)),
            'health': hud_region.crop((int(width * 0.25), 0, int(width * 0.40), hud_height)),
            'armor': hud_region.crop((int(width * 0.60), 0, int(width * 0.75), hud_height))
        }
        
        return sections
        
    def ocr_number(self, image: Image.Image) -> Optional[int]:
        """Extract number from image using OCR"""
        try:
            # Preprocess for better OCR
            # Convert to grayscale, increase contrast
            text = pytesseract.image_to_string(image, config='--psm 7 -c tessedit_char_whitelist=0123456789%')
            
            # Extract numbers
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
                
        except Exception as e:
            logging.debug(f"OCR failed: {e}")
            
        return None
        
    def read_game_state(self) -> Optional[DoomState]:
        """Extract current game state from screen"""
        if not PIL_AVAILABLE:
            # Return mock data if OCR not available
            self.tick_counter += 1
            return DoomState(
                tick=self.tick_counter,
                player_x=0,
                player_y=0,
                player_z=0,
                player_angle=0,
                health=100,
                armor=50,
                ammo=[50, 20, 100, 40],
                current_weapon=2,
                level=1
            )
            
        screenshot = self.capture_doom_window()
        if not screenshot:
            return self.last_state
            
        hud_sections = self.extract_hud_region(screenshot)
        
        # Extract values from HUD
        health = self.ocr_number(hud_sections['health']) or 100
        armor = self.ocr_number(hud_sections['armor']) or 0
        ammo = self.ocr_number(hud_sections['ammo']) or 50
        
        self.tick_counter += 1
        
        state = DoomState(
            tick=self.tick_counter,
            player_x=0,  # Can't determine from screen
            player_y=0,
            player_z=0,
            player_angle=0,
            health=health,
            armor=armor,
            ammo=[ammo, 20, 100, 40],  # Only current ammo visible
            current_weapon=2,  # Would need to detect from screen
            level=1  # E1M1
        )
        
        self.last_state = state
        return state


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    reader = DoomOCRReader()
    
    print("DOOM OCR Reader Test")
    print("Make sure DOOM is running and visible")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            state = reader.read_game_state()
            if state:
                print(f"Tick: {state.tick}, Health: {state.health}, "
                      f"Armor: {state.armor}, Ammo: {state.ammo[0]}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDone")