# TASK: Project 2 (AURA Lite MCP - Real-Time Weather Fetcher)
"""
weather_tool.py
---------------
Fetches real-time weather data using WeatherAPI.com.
Returns temperature, rainfall classification, and condition details.
"""

import httpx
from app.utils.logger import get_logger

logger = get_logger(__name__)

API_KEY = "94052f2ea2ec4c86bc091837262703"
WEATHER_URL = "http://api.weatherapi.com/v1/current.json"
MAX_RETRIES = 1


def _classify_rainfall(precip_mm: float) -> str:
    """Classify rainfall intensity from mm to low/medium/high."""
    if precip_mm < 2.5:
        return "low"
    elif precip_mm < 7.5:
        return "medium"
    else:
        return "high"


async def get_weather(location: str) -> dict:
    """
    Fetch real-time weather for a location using WeatherAPI.com.

    Returns:
        {
            "location": str,
            "temperature": float,
            "feels_like": float,
            "rainfall": "low" | "medium" | "high",
            "humidity": int,
            "description": str
        }
    """
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            logger.info(f"[WeatherTool] Fetching weather for '{location}' (attempt {attempt + 1})")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    WEATHER_URL,
                    params={"key": API_KEY, "q": location},
                )
                response.raise_for_status()

            data = response.json()

            # Check for API-level errors
            if "error" in data:
                raise RuntimeError(data["error"]["message"])

            loc = data["location"]
            cur = data["current"]

            temp_c = float(cur.get("temp_c", 0))
            feels_like = float(cur.get("feelslike_c", 0))
            precip_mm = float(cur.get("precip_mm", 0))
            humidity = int(cur.get("humidity", 0))
            condition = cur.get("condition", {}).get("text", "Unknown")

            result = {
                "location": f"{loc['name']}, {loc.get('region', '')}, {loc['country']}".strip(", "),
                "temperature": temp_c,
                "feels_like": feels_like,
                "rainfall": _classify_rainfall(precip_mm),
                "humidity": humidity,
                "description": condition,
            }
            logger.info(f"[WeatherTool] Result: {temp_c}°C, {condition}, precip={precip_mm}mm → {result['rainfall']}")
            return result

        except Exception as e:
            last_error = e
            logger.warning(f"[WeatherTool] Attempt {attempt + 1} failed: {e}")

    logger.error(f"[WeatherTool] All attempts failed for '{location}'.")
    raise RuntimeError(f"Weather API failed for '{location}': {last_error}")
