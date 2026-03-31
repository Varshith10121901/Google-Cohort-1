# TASK: Project 2 (AURA Lite MCP - Server Exposing Tools)
"""
server.py
---------
MCP Server interface exposing local crop tools to MCP Clients.
In a distributed setup, this is run over Stdio/SSE.
For this container architecture, it exposes functions as an internal API.
"""

from integrations.mcp.tools.weather_tool import get_weather
from integrations.mcp.tools.crop_tool import get_crop_from_json
from integrations.mcp.tools.ai_fallback import get_crop_from_ai

# Exposed server endpoints
async def get_weather_endpoint(location: str) -> dict:
    """MCP Server Endpoint: Fetch weather data."""
    return await get_weather(location)

def get_crop_from_json_endpoint(location: str, temperature: float, rainfall: str) -> dict:
    """MCP Server Endpoint: Fetch crops from JSON database."""
    return get_crop_from_json(location, temperature, rainfall)

async def get_crop_from_ai_endpoint(temperature: float, rainfall: str) -> dict:
    """MCP Server Endpoint: Fetch crops using Gemini AI fallback."""
    return await get_crop_from_ai(temperature, rainfall)
