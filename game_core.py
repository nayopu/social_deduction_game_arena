#!/usr/bin/env python3
"""
Game Core Logic
--------------
Main game execution and coordination.
"""

import asyncio
import json
import random
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

from agents import Player, GameSystem
from llm_utils import create_llm, parse_model_spec
from simple_logging import GameLogger, log_info, log_error
from config import DEFAULT_PLAYER_MODEL, DEFAULT_GM_MODEL, DEFAULT_MAX_TURNS, DEFAULT_NUM_PLAYERS


async def parallel_bidding(agents: Dict[str, Player], turn: int) -> Dict[str, dict]:
    """Execute bidding phase in parallel for all player agents"""
    with ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = {}
        for name, agent in agents.items():
            future = executor.submit(agent.decide, turn)
            futures[name] = future
        
        results = {}
        for name, future in futures.items():
            try:
                results[name] = future.result()
            except Exception as e:
                log_error(f"Agent {name} failed to bid: {e}")
                results[name] = {"bid": 0.0, "msg": "", "to": "ALL", "reason": "Error"}
        
        return results


async def run_game(rules_file: str, 
                  num_players: int = DEFAULT_NUM_PLAYERS,
                  player_model: str = DEFAULT_PLAYER_MODEL, 
                  gm_model: str = DEFAULT_GM_MODEL,
                  out_dir: str = "game_logs", 
                  max_turns: int = DEFAULT_MAX_TURNS) -> Dict[str, Any]:
    """
    Run a complete social deduction game.
    
    Args:
        rules_file: Path to the rules file
        num_players: Number of players
        player_model: Model spec for players
        gm_model: Model spec for GM (uses player_model if None)
        out_dir: Output directory for logs
        max_turns: Maximum number of turns
    
    Returns:
        Dict with game results
    """
    try:
        # Load rules
        if not Path(rules_file).exists():
            rules_file = f"sample_rules/{rules_file}"
        
        with open(rules_file, 'r') as f:
            rules_content = f.read()
        
        # Parse model specifications
        player_api, player_model_name = parse_model_spec(player_model)
        if gm_model:
            gm_api, gm_model_name = parse_model_spec(gm_model)
        else:
            gm_api, gm_model_name = player_api, player_model_name
        
        # Create LLMs
        player_llm = create_llm(player_api, player_model_name)
        gm_llm = create_llm(gm_api, gm_model_name)
        
        # Create logger
        logger = GameLogger(out_dir)
        
        # Create agents
        agents = {}
        for i in range(num_players):
            name = f"P{i+1}"
            agents[name] = Player(name, rules_content, player_llm)
        
        game_system = GameSystem(rules_content, gm_llm)
        
        # Initialize roles (simple random assignment for now)
        roles = {f"P{i+1}": f"Role{i+1}" for i in range(num_players)}
        logger.log_setup(roles)
        
        log_info(f"Starting game with {num_players} players")
        
        # Main game loop
        winner = None
        for turn in range(1, max_turns + 1):
            log_info(f"\n=== Turn {turn} ===")
            
            # Bidding phase
            all_submissions = await parallel_bidding(agents, turn)
            
            # System decision phase
            system_response = game_system.process_turn_with_all_submissions(all_submissions)
            
            # Execute selected messages
            selected_messages = system_response.get("selected_messages", [])
            for msg_info in selected_messages:
                speaker = msg_info["speaker"]
                recipients = msg_info["to"]
                message = msg_info["message"]
                
                # Log the message
                recipients_str = ",".join(recipients) if isinstance(recipients, list) else str(recipients)
                logger.log_message(turn, speaker, recipients_str, message)
                
                # Add to memory logs
                for agent_name, agent in agents.items():
                    agent.mem_log.append((turn, speaker, recipients_str, message))
                game_system.mem_log.append((turn, speaker, recipients_str, message))
            
            # Check for winner
            winner = system_response.get("winner")
            if winner:
                log_info(f"Game ended with winner: {winner}")
                break
        
        # Game end
        completed = winner is not None
        logger.log_game_end(winner, turn)
        logger.close()
        
        # Save game summary
        summary = {
            "success": True,
            "game_completed": completed,
            "winner": winner,
            "turn_count": turn,
            "max_turns": max_turns,
            "max_turns_reached": not completed,
            "total_messages": len([msg for msg in game_system.mem_log if msg[1] != "SYSTEM"]),
            "players": list(agents.keys()),
            "rules_file": rules_file
        }
        
        with open(Path(out_dir) / "game_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
        
    except Exception as e:
        log_error(f"Game failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "game_completed": False,
            "winner": None,
            "turn_count": 0
        }


async def main():
    """Main entry point for running games"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run social deduction game")
    parser.add_argument("--rules", type=str, required=True, help="Rules file")
    parser.add_argument("--players", type=int, default=DEFAULT_NUM_PLAYERS, help="Number of players")
    parser.add_argument("--player-model", type=str, default=DEFAULT_PLAYER_MODEL, help="Player model")
    parser.add_argument("--gm-model", type=str, default=DEFAULT_GM_MODEL, help="GM model")
    parser.add_argument("--out-dir", type=str, default="game_logs", help="Output directory")
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS, help="Max turns")
    
    args = parser.parse_args()
    
    result = await run_game(
        rules_file=args.rules,
        num_players=args.players,
        player_model=args.player_model,
        gm_model=args.gm_model,
        out_dir=args.out_dir,
        max_turns=args.max_turns
    )
    
    print(f"Game completed: {result}")


if __name__ == "__main__":
    asyncio.run(main()) 