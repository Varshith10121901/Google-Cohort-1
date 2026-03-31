# TASK: Project 2 (AURA Lite MCP - MCP Client wrapper)
"""
mcp_client.py
-------------
Acts as the MCP Client, connecting the ADK agent to the MCP Server endpoints.
Registers server endpoints as ADK-compatible tools.
"""

import integrations.mcp.server as mcp_server


async def get_weather(location: str) -> dict:
    """
    Fetch real-time weather data (temperature, rainfall) for a location.
    Must be called first to get the environmental conditions.
    """
    return await mcp_server.get_weather_endpoint(location)


def get_crop_from_json(location: str, temperature: float, rainfall: str) -> dict:
    """
    Query local JSON database for crops matching temperature and rainfall.
    Call this immediately after get_weather, using the exact normalized `location` returned by get_weather.
    """
    return mcp_server.get_crop_from_json_endpoint(location, temperature, rainfall)


async def get_crop_from_ai(temperature: float, rainfall: str) -> dict:
    """
    Fallback AI Crop Suggester: Ask Gemini for crop suggestions.
    ONLY CALL THIS if `get_crop_from_json` returns an empty 'recommended_crops' list.
    """
    return await mcp_server.get_crop_from_ai_endpoint(temperature, rainfall)


# Exported tools for ADK Farmer Agent
mcp_tools = [get_weather, get_crop_from_json, get_crop_from_ai]
