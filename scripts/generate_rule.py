#!/usr/bin/env python3
"""
Rule Generator for Social Deduction Games

This script generates Python rule files from game ideas using LLM.
Extracted from experiment.py to be a standalone utility.
"""

import argparse
import sys
from pathlib import Path

# Import LLM utilities from the unified client
from llm_client import get_llm_client
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage


def generate_rule_file(description: str, output_path: str) -> bool:
    """
    Generate a Python rule file from the game idea using LLM.
    
    Args:
        description: Plain text description of the game mechanics and rules
        output_path: Path where to save the generated rule file
        
    Returns:
        bool: True if successful, raises exception if failed
    """
    # Generate a simple game name from the output path
    output_filename = Path(output_path).stem
    game_name = output_filename if output_filename != "rule" else "custom_game"
    title = f"Generated Social Deduction Game: {game_name.replace('_', ' ').title()}"
    
    try:
        # Create LangChain LLM client using unified configuration
        # Get client from unified configuration
        client, model_name = get_llm_client()
        
        # Check if model supports temperature parameter
        # o3-mini and similar models don't support temperature
        supports_temperature = not (model_name.startswith("o3") or model_name.startswith("o1"))
        
        # Create LangChain wrapper for the configured client
        if "claude" in model_name:
            if supports_temperature:
                llm_client = ChatAnthropic(
                    model=model_name,
                    temperature=0.1,
                    anthropic_api_key=client.api_key
                )
            else:
                llm_client = ChatAnthropic(
                    model=model_name,
                    anthropic_api_key=client.api_key
                )
        else:
            # For OpenAI-compatible APIs (including OpenRouter, DeepSeek, etc.)
            base_url = getattr(client, 'base_url', None)
            # Convert URL object to string if needed
            if base_url is not None:
                base_url = str(base_url)
            
            if supports_temperature:
                llm_client = ChatOpenAI(
                    model=model_name,
                    temperature=0.1,
                    openai_api_key=client.api_key,
                    openai_api_base=base_url
                )
            else:
                llm_client = ChatOpenAI(
                    model=model_name,
                    openai_api_key=client.api_key,
                    openai_api_base=base_url
                )
        
        # Read all text files in sample_rules directory and create a dictionary
        sample_rules_dir = Path(__file__).parent / "sample_rules"
        rule_examples = {}
        for rule_file in sample_rules_dir.glob("*.txt"):
            with open(rule_file, 'r') as f:
                rule_examples[rule_file.stem] = f.read()
        
        rule_examples_str = '\n\n'.join([f"**{key}.txt**\n```\n{rule_examples[key]}\n```" for key in rule_examples.keys()])
        
        # Create a detailed prompt for the LLM to generate the rule file
        prompt = f"""GAME IDEA TO IMPLEMENT:
Name: {game_name}
Title: {title}
Description: {description}

EXAMPLE STRUCTURES:
{rule_examples_str}

DETAILED REQUIREMENTS:

Follow the exact text file structure shown in the example files above. Your output should be a complete game rules text file that follows this format:

1. HEADER: Start with a decorative title using equal signs (=) as borders, like:
   ================ [Game Name] Game Rules ================

2. OVERVIEW: Brief description of the game concept and core mechanics

3. VICTORY CONDITIONS: Clear win/loss conditions for each faction/team

4. ROLES AND ABILITIES: Detailed description of all roles in the game, organized by faction/team:
   - Use the exact role names from the game description
   - Each role should have specific abilities and faction alignments
   - Include any special information or abilities described in the game idea

5. GAME PHASES: Step-by-step breakdown of how the game flows:
   - List each phase in chronological order
   - Explain what happens in each phase
   - Include timing and sequencing details

6. RESOLUTION: How votes, actions, and conflicts are resolved

7. GAME FLOW: Brief summary of the overall game sequence

8. COMMUNICATION RULES: Guidelines for player communication during different phases

9. GM RESPONSIBILITIES: Comprehensive guide for the Game Master including:
   - Phase Management with example announcements
   - Special Role Coordination details
   - Game Setup instructions with player count recommendations
   - Game End conditions and victory announcements
   - Rule Enforcement guidelines

10. ADDITIONAL SECTIONS: Include any game-specific elements like:
    - Team size tables (for mission-based games)
    - Location lists (for location-based games)
    - Special guidelines or clarifications

11. FOOTER: End with a line of equal signs (=)

CRITICAL RULES:
- NO placeholder content like [ROLE_1], [FACTION_1] - use actual role names from the game idea
- NO generic roles - implement the specific roles described in the game concept
- Include complete victory conditions, not placeholders
- Write full rule descriptions, not outlines
- The file must be immediately usable for game play
- Follow the text format structure exactly as shown in the examples
- Include specific GM announcement examples
- Provide clear role assignment guidelines based on player count

Generate a complete game rules text file that implements this specific social deduction game idea. The output should be formatted as plain text following the structure of the example files."""

        # Get LLM response using LangChain API
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an experienced game designer. Please convert the given game idea into a complete social deduction game rule file. Follow the provided example structure exactly and implement specific game mechanics without using placeholders."),
            ("human", "{prompt}")
        ])
        
        chain = prompt_template | llm_client
        response = chain.invoke({"prompt": prompt})
        
        # Extract content from response
        if hasattr(response, 'content'):
            generated_code = response.content
        else:
            generated_code = str(response)
        
        # Clean up the response (remove markdown code blocks if present)
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0]
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0]
        
        # Write the generated rule file
        with open(output_path, 'w') as f:
            f.write(generated_code.strip())
        
        print(f"Generated rule file using LLM ({model_name}): {output_path}")
        return True
        
    except Exception as e:
        print(f"Error generating rule file with LLM: {e}")
        raise e  # Re-raise the error instead of falling back


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Python rule files for social deduction games from game descriptions using LLM. "
                   "You can provide the description via --description argument or pipe it through stdin."
    )
    parser.add_argument(
        "--description", 
        type=str, 
        help="Plain text description of the game mechanics, roles, and rules (or pipe via stdin)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        required=True,
        help="Path where to save the generated rule file (e.g., my_game.py)"
    )
    return parser.parse_args()


def main():
    """Main function for standalone usage."""
    args = parse_args()
    
    # Get the description from command line or stdin
    if args.description:
        description = args.description.strip()
    else:
        # Read from stdin
        try:
            description = sys.stdin.read().strip()
        except Exception as e:
            print(f"Error reading from stdin: {e}")
            sys.exit(1)
    
    # Validate description is not empty
    if not description:
        print("Error: Game description cannot be empty. Provide via --description or pipe through stdin.")
        sys.exit(1)
    
    # Convert output path to Path object
    output_path = Path(args.output)
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"Generating rule file from description...")
        print(f"Description: {description[:100]}{'...' if len(description) > 100 else ''}")
        print(f"Output path: {output_path}")
        
        success = generate_rule_file(description, str(output_path))
        
        if success:
            print(f"\nRule file generated successfully!")
            print(f"You can now use this rule file with the social deduction game system.")
        else:
            print("Failed to generate rule file.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during rule generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 