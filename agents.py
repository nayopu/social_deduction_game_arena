#!/usr/bin/env python3
"""
Game Agents
----------
Agent classes for social deduction games.
"""

import time
import asyncio
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage
from langchain.output_parsers.json import SimpleJsonOutputParser

from llm_utils import clean_json_response
from simple_logging import log_warning
from config import MAX_RETRIES, MAX_HISTORY_TURNS
from prompts import (
    PLAYER_SYSTEM_PROMPT, PLAYER_HUMAN_PROMPT,
    GAMEMASTER_SYSTEM_PROMPT, GAMEMASTER_HUMAN_PROMPT
)


class AgentResponse(BaseModel):
    """Validated agent response model"""
    bid: float = Field(ge=0.0, le=1.0)
    msg: str
    to: str
    reason: str = ""

    @classmethod
    def from_llm_response(cls, response: Any) -> 'AgentResponse':
        """Create AgentResponse from LLM response with validation"""
        if isinstance(response, str):
            response = clean_json_response(response)
        
        if not isinstance(response, dict):
            log_warning(f"Invalid response type: {type(response)}")
            return cls(bid=0.0, msg="", to="ALL", reason="Invalid response format")
        
        # Ensure required fields exist with defaults
        response = {
            "bid": float(response.get("bid", 0.0)),
            "msg": str(response.get("msg", "")),
            "to": str(response.get("to", "ALL")),
            "reason": str(response.get("reason", ""))
        }
        
        # Validate bid range
        response["bid"] = max(0.0, min(1.0, response["bid"]))
        
        return cls(**response)


class Agent:
    """Base agent class"""
    def __init__(self, name: str, llm: ChatOpenAI):
        self.name = name
        self.llm = llm
        self.mem_log: List[Tuple[int, str, str, str]] = []  # (turn, sender, recipients, text)
        self.max_retries = MAX_RETRIES

    async def decide_async(self, turn: int) -> dict:
        """Make a decision asynchronously"""
        history = "\n".join(f"{turn}: {sender}▶{recv}: {txt}" 
                           for turn, sender, recv, txt in self.mem_log[-MAX_HISTORY_TURNS:])
        
        for attempt in range(self.max_retries):
            try:
                js = await self.main_chain.ainvoke({"history": history})
                response = AgentResponse.from_llm_response(js)
                return response.model_dump()
                
            except Exception as e:
                log_warning(f"Error in agent {self.name}'s response (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "bid": 0.0,
                        "msg": "", 
                        "to": "ALL",
                        "reason": f"Error after {self.max_retries} attempts"
                    }
                await asyncio.sleep(0.5)

    def decide(self, turn: int) -> dict:
        """Make a decision synchronously"""
        history = "\n".join(f"{turn}: {sender}▶{recv}: {txt}" 
                           for turn, sender, recv, txt in self.mem_log[-MAX_HISTORY_TURNS:])
        
        for attempt in range(self.max_retries):
            try:
                js = self.main_chain.invoke({"history": history})
                response = AgentResponse.from_llm_response(js)
                return response.model_dump()
                
            except Exception as e:
                log_warning(f"Error in agent {self.name}'s response (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "bid": 0.0,
                        "msg": "",
                        "to": "ALL",
                        "reason": f"Error after {self.max_retries} attempts"
                    }
                time.sleep(0.5)


class Player(Agent):
    """Player agent"""
    def __init__(self, name: str, rules_content: str, llm: ChatOpenAI):
        super().__init__(name, llm)
        parser = SimpleJsonOutputParser()
        
        sys_prompt = PLAYER_SYSTEM_PROMPT.format(player_name=name, rules_content=rules_content)
        human_prompt = PLAYER_HUMAN_PROMPT
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=sys_prompt),
            ("human", human_prompt)
        ])
        self.main_chain = prompt | llm | parser


class GameMaster(Agent):
    """GameMaster/GM agent"""
    def __init__(self, rules_content: str, llm: ChatOpenAI):
        super().__init__("GM", llm)
        
        sys_prompt = GAMEMASTER_SYSTEM_PROMPT.format(rules_content=rules_content)
        human_prompt = GAMEMASTER_HUMAN_PROMPT
        
        self.system_chain = ChatPromptTemplate.from_messages([
            SystemMessage(content=sys_prompt),
            ("human", human_prompt)
        ]) | llm | SimpleJsonOutputParser()
    
    def process_turn_with_all_submissions(self, all_submissions: Dict) -> dict:
        """Process a turn with all player submissions"""
        history = "\n".join(f"{turn}: {sender}▶{recv}: {txt}" 
                    for turn, sender, recv, txt in self.mem_log[-MAX_HISTORY_TURNS:])
        
        # Format submissions
        submissions_text = []
        for agent_name, submission in all_submissions.items():
            bid = submission.get("bid", 0.0)
            msg = submission.get("msg", "").strip()
            to = submission.get("to", "ALL")
            reason = submission.get("reason", "")
            submissions_text.append(f"{agent_name}: bid={bid}, to={to}, msg='{msg}', reason='{reason}'")
        
        submissions_str = "\n".join(submissions_text)
        
        for attempt in range(self.max_retries):
            try:
                response = self.system_chain.invoke({
                    "history": history,
                    "all_submissions": submissions_str
                })
                
                if isinstance(response, str):
                    response = clean_json_response(response)
                
                if not response or not isinstance(response, dict):
                    log_warning(f"Invalid GameMaster response (attempt {attempt + 1})")
                    if attempt == self.max_retries - 1:
                        return {"selected_messages": [], "reason": "Failed to get valid response"}
                    time.sleep(0.5)
                    continue
                
                # Validate response structure
                if "selected_messages" not in response:
                    response["selected_messages"] = []
                
                if not isinstance(response["selected_messages"], list):
                    response["selected_messages"] = []
                
                # Validate each message
                valid_messages = []
                for msg in response["selected_messages"]:
                    if isinstance(msg, dict) and "speaker" in msg and "to" in msg and "message" in msg:
                        # Ensure 'to' is a list
                        if isinstance(msg["to"], str):
                            if msg["to"] == "ALL":
                                msg["to"] = ["ALL"]
                            else:
                                msg["to"] = [x.strip() for x in msg["to"].split(",")]
                        elif not isinstance(msg["to"], list):
                            msg["to"] = ["ALL"]
                        valid_messages.append(msg)
                
                response["selected_messages"] = valid_messages
                
                # Ensure required fields
                if "reason" not in response:
                    response["reason"] = "No reason provided"
                if "winner" not in response:
                    response["winner"] = None
                
                return response
                
            except Exception as e:
                log_warning(f"Error in GameMaster processing (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return {"selected_messages": [], "reason": f"GameMaster error: {str(e)}"}
                time.sleep(0.5) 