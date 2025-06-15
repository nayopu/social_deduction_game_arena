#!/usr/bin/env python3
"""
Simple Game Logging
------------------
Clean, simple logging for social deduction games.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class GameLogger:
    """Simple game logger - just log what you need"""
    
    def __init__(self, out_dir: str):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        # Open log files
        self.summary_file = open(self.out_dir / "game_summary.txt", 'w')
        self.json_file = open(self.out_dir / "game_log.json", 'w')
        self.json_file.write("[\n")
        self.first_entry = True
        
        self.summary_file.write("=== GAME LOG ===\n\n")
    
    def log_message(self, turn: int, speaker: str, recipients: str, message: str):
        """Log a message"""
        log_line = f"[{turn:02d}] {speaker}▶{recipients}: {message}\n"
        self.summary_file.write(log_line)
        self.summary_file.flush()
        print(log_line.strip())
        
        # Also log to JSON
        self._log_json({
            "turn": turn,
            "speaker": speaker, 
            "recipients": recipients,
            "message": message
        })
    
    def log_game_end(self, winner: Optional[str], total_turns: int):
        """Log game end"""
        if winner:
            end_msg = f"\nGAME END: Winner = {winner} (Turn {total_turns})\n"
        else:
            end_msg = f"\nGAME END: No winner after {total_turns} turns\n"
        
        self.summary_file.write(end_msg)
        self.summary_file.flush()
        print(end_msg.strip())
    
    def _log_json(self, data: Dict[str, Any]):
        """Add entry to JSON log"""
        if not self.first_entry:
            self.json_file.write(",\n")
        else:
            self.first_entry = False
        json.dump(data, self.json_file, indent=2)
        self.json_file.flush()
    
    def close(self):
        """Close log files"""
        self.json_file.write("\n]\n")
        self.json_file.close()
        self.summary_file.close()


# Simple console logging functions
def log_info(message: str):
    """Log info message"""
    print(message)

def log_warning(message: str):
    """Log warning message"""
    print(f"Warning: {message}")

def log_error(message: str):
    """Log error message"""
    print(f"Error: {message}") 