#!/usr/bin/env python3
"""
LLM Utilities
------------
Helper functions for LLM management and response processing.
"""

import os
import re
import json
from typing import Tuple
from langchain_openai import ChatOpenAI
from simple_logging import log_warning


def create_llm(api_source: str, model_name: str, temperature: float = 0.1) -> ChatOpenAI:
    """Create an LLM instance based on API source and model name"""
    api_source = api_source.lower()
    supports_temperature = not model_name.startswith("o3")
    
    if api_source == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        if supports_temperature:
            return ChatOpenAI(
                model_name=model_name,
                openai_api_key=api_key,
                temperature=temperature
            )
        else:
            return ChatOpenAI(
                model_name=model_name,
                openai_api_key=api_key
            )
    elif api_source == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        if supports_temperature:
            return ChatOpenAI(
                model_name=model_name,
                openai_api_base="https://openrouter.ai/api/v1",
                openai_api_key=api_key,
                temperature=temperature,
                default_headers={
                    "HTTP-Referer": "https://github.com/your-repo",
                    "X-Title": "Social Deduction Game"
                }
            )
        else:
            return ChatOpenAI(
                model_name=model_name,
                openai_api_base="https://openrouter.ai/api/v1",
                openai_api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/your-repo",
                    "X-Title": "Social Deduction Game"
                }
            )
    else:
        raise ValueError(f"Unsupported API source: {api_source}")


def parse_model_spec(model_spec: str) -> Tuple[str, str]:
    """Parse model specification string into API source and model name"""
    if ':' not in model_spec:
        raise ValueError(f"Invalid model specification: {model_spec}")
    
    api_source, model_name = model_spec.split(':', 1)
    return api_source.strip(), model_name.strip()


def clean_json_response(response: str) -> dict:
    """Clean and validate JSON response from LLM"""
    if not isinstance(response, str):
        return {}
        
    # Remove text before first { and after last }
    response = re.sub(r'^[^{]*({.*})[^}]*$', r'\1', response, flags=re.DOTALL)
    
    # Remove markdown code blocks
    response = re.sub(r"```json\s*|\s*```", "", response)
    
    # Remove trailing commas
    response = re.sub(r",\s*}", "}", response)
    response = re.sub(r",\s*]", "]", response)
    
    # Remove invalid control characters
    response = re.sub(r"[\x00-\x1F\x7F]", "", response)
    
    # Fix missing quotes around keys
    response = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', response)
    
    # Fix single quotes to double quotes
    response = re.sub(r"'", '"', response)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        log_warning(f"JSON cleaning failed: {e}")
        # Try aggressive cleaning
        try:
            response = re.sub(r'[^{}\[\]",:0-9\s]', '', response)
            return json.loads(response)
        except json.JSONDecodeError:
            return {} 