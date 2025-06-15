#!/usr/bin/env python3
"""
Simple Configuration
-------------------
Centralized settings for the social deduction game system.
"""

# Game Settings
DEFAULT_MAX_TURNS = 100
DEFAULT_NUM_PLAYERS = 5
DEFAULT_NUM_GAME_RUNS = 5

# Model Settings
DEFAULT_PLAYER_MODEL = "openrouter:deepseek/deepseek-r1-0528"
DEFAULT_GM_MODEL = None  # Use same as player if None

# LLM Settings
DEFAULT_TEMPERATURE = 0.1
MAX_RETRIES = 3
MAX_HISTORY_TURNS = 30

# Directory Settings
SAMPLE_RULES_DIR = "sample_rules"
GAME_LOGS_DIR = "game_logs"

# Bidding Settings
MIN_BID = 0.0
MAX_BID = 1.0 