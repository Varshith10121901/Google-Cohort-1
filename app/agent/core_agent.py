# TASK: Project 1 & 2 (AURA Lite Core - ADK Agent Setup)
"""
core_agent.py
-------------
Defines the AURA Lite agents (Summarizer and Farmer).
Uses APIKeyManager to dynamically pick the current model.
"""

from google.adk.agents import Agent

from app.agent.prompts import SYSTEM_PROMPT, FARMER_AGENT_PROMPT
from app.agent.tools import clean_text
from app.agent.mcp_client import mcp_tools
from app.config.api_key_manager import key_manager


def build_summarizer_agent() -> Agent:
    """Project 1: Build the AURA Lite Core Summarization Agent."""
    return Agent(
        name="aura_lite",
        model=key_manager.current_model,
        description="AURA Lite: a precise text summarization agent.",
        instruction=SYSTEM_PROMPT,
        tools=[clean_text],
    )


def build_farmer_agent() -> Agent:
    """Project 2: Build the AURA Farmer Agent powered by MCP tools."""
    return Agent(
        name="aura_farmer",
        model=key_manager.current_model,
        description="AURA Farmer: a weather-based smart crop recommendation agent.",
        instruction=FARMER_AGENT_PROMPT,
        tools=mcp_tools,
    )


# Backward compatibility for InferenceService
def build_agent() -> Agent:
    return build_summarizer_agent()
