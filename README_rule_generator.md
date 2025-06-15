# Rule Generator for Social Deduction Games

This repository now includes a dedicated rule generator script that has been extracted from the main experiment system to provide a standalone utility for generating game rules.

## What Changed

The rule generation functionality has been extracted from `experiment.py` into a dedicated `rule_generator.py` script for better modularity and reusability.

### Files Modified/Created:
- **`rule_generator.py`** - New standalone script for generating rule files
- **`experiment.py`** - Updated to import and use the rule generator
- **`example_game_description.txt`** - Example game description file for testing

## Usage

### Command Line Interface

Generate a rule file from a description string:
```bash
python rule_generator.py --description "A social deduction game where players are divided into two teams..." --output my_game_rules.py
```

Generate a rule file from a text file:
```bash
python rule_generator.py --description-file example_game_description.txt --output spy_infiltration_rules.py
```

### Programmatic Usage

You can also import and use the rule generator in your own Python code:

```python
from rule_generator import generate_rule_file

description = "A social deduction game where players are divided into two teams..."

success = generate_rule_file(description, "output/my_rules.py")
if success:
    print("Rule file generated successfully!")
```

## Game Description Format

The game description should be a plain text description that includes:

- **Game mechanics**: How the game works, what phases it has
- **Roles**: What roles exist and what they can do
- **Victory conditions**: How each team/faction wins
- **Gameplay flow**: How a typical game progresses

### Example Game Description

```
A social deduction game where Spies try to infiltrate and sabotage Government Agents' mission while Agents try to identify and eliminate the Spies. Each night, Agents can investigate other players to learn their true identity, while Spies can sabotage the mission progress. The Government team wins by completing their mission objectives while eliminating all Spies. The Spy team wins by either eliminating enough Agents or sabotaging the mission completely. The game features hidden role cards, secret communications between teammates, and a mission progress tracker that determines the overall game outcome.
```

## Features

- **LLM-Powered Generation**: Uses your configured LLM (OpenAI, Anthropic, OpenRouter, etc.) to generate complete rule files
- **Template-Based**: Uses existing sample rules as templates to ensure proper structure
- **Complete Rule Files**: Generates immediately playable Python rule files with all required functions
- **Error Handling**: Comprehensive error checking and validation
- **Flexible Input**: Accepts JSON strings or JSON files as input

## Dependencies

The rule generator requires the same dependencies as the main experiment system:
- `llm_client` (unified LLM client)
- `langchain_openai` 
- `langchain_anthropic`
- `langchain`

## Integration with Experiments

The main `experiment.py` still uses the rule generator automatically when needed, but now imports it as a separate module for better code organization.

## Testing the Rule Generator

Try generating a rule file with the provided example:

```bash
python rule_generator.py --description-file example_game_description.txt --output test_spy_game.py
```

This will create a complete rule file that you can then use with the social deduction game system. 