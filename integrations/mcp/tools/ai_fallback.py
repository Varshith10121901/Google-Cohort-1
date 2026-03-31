# TASK: Project 2 (AURA Lite MCP - Gemini AI Fallback)
"""
ai_fallback.py
--------------
When the JSON crop database has no matching crops, this module
calls Gemini AI to generate intelligent crop recommendations.
Acts as the FALLBACK layer in the hybrid architecture.
Supports automatic API key rotation and model fallback on 429 errors.
"""

import json
import os
import asyncio
from google import genai
from app.config.api_key_manager import key_manager, is_quota_error
from app.utils.logger import get_logger

logger = get_logger(__name__)

CROP_AI_PROMPT = """You are an expert Indian agricultural advisor.

Given the following weather conditions:
- Temperature: {temperature}°C
- Rainfall: {rainfall}

Suggest exactly 3 suitable crops that can be grown in India under these conditions.

For each crop, provide:
1. name: The crop name
2. profit_per_acre: Estimated profit in INR per acre
3. season: Growing season (Kharif/Rabi/Year-round)
4. description: One-line farming advice

IMPORTANT: Return ONLY a valid JSON array with exactly 3 objects. No markdown, no explanation.
Example format:
[
  {{"name": "Mango", "profit_per_acre": 100000, "season": "Annual", "description": "Tropical fruit crop."}}
]
"""


async def get_crop_from_ai(temperature: float, rainfall: str) -> dict:
    """
    Use Gemini to suggest crops when JSON dataset has no match.
    Automatically rotates API keys and models on 429 quota errors.

    Args:
        temperature: Current temperature in Celsius.
        rainfall: "low", "medium", or "high".

    Returns:
        {
            "recommended_crops": [...],
            "source": "ai"
        }
    """
    logger.info(f"[AIFallback] Calling Gemini for temp={temperature}, rainfall={rainfall}")

    max_attempts = key_manager.get_total_combinations() + 2
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            current_key = key_manager.current_key
            current_model = key_manager.current_model

            if not current_key:
                raise RuntimeError("No GOOGLE_API_KEY configured for AI fallback.")

            client = genai.Client(api_key=current_key)
            prompt = CROP_AI_PROMPT.format(temperature=temperature, rainfall=rainfall)

            logger.info(
                f"[AIFallback] Attempt {attempt}: Model={current_model}, "
                f"Key=...{current_key[-6:]}"
            )

            response = await client.aio.models.generate_content(
                model=current_model,
                contents=prompt,
            )

            raw_text = response.text.strip()
            logger.info(f"[AIFallback] Raw Gemini response: {raw_text[:200]}")

            # Clean markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            crops = json.loads(raw_text)

            result = {
                "recommended_crops": [
                    {
                        "name": c.get("name", "Unknown"),
                        "profit_per_acre": c.get("profit_per_acre", 0),
                        "season": c.get("season", "Unknown"),
                        "description": c.get("description", ""),
                    }
                    for c in crops[:3]
                ],
                "source": "ai",
            }
            logger.info(f"[AIFallback] Returning {len(result['recommended_crops'])} AI-recommended crops.")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[AIFallback] Failed to parse Gemini response as JSON: {e}")
            last_exception = RuntimeError(f"AI fallback returned unparseable response: {e}")
            if attempt >= 3:
                raise last_exception
            await asyncio.sleep(1)
        except Exception as e:
            last_exception = e
            if is_quota_error(e):
                logger.warning(
                    f"[AIFallback] Attempt {attempt}: Quota error. Rotating... "
                    f"Error: {str(e)[:100]}"
                )
                key_manager.rotate()
                await asyncio.sleep(2)
            else:
                logger.error(f"[AIFallback] Gemini call failed: {e}")
                if attempt >= 3:
                    raise RuntimeError(f"AI fallback failed: {e}")
                await asyncio.sleep(1)

    raise RuntimeError(f"AI fallback exhausted all API key combinations: {last_exception}")
