# TASK: Project 3 (AURA Lite - SQL Agent)
"""
sql_agent.py
------------
Uses Gemini to convert natural language questions into SQL queries.
Targets the 'crops' table with strict SELECT-only output.
Supports automatic API key rotation and model fallback on 429 errors.
"""

import os
from google import genai
from app.agent.prompts import SQL_AGENT_PROMPT
from app.config.api_key_manager import key_manager, is_quota_error
from app.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)


async def generate_sql_from_question(question: str) -> str:
    """
    Sends a natural language question to Gemini and returns a raw SQL SELECT query.
    Automatically rotates API keys and models on 429 quota errors.
    """
    max_attempts = key_manager.get_total_combinations() + 2
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            # Always use the current key and model from the manager
            current_key = key_manager.current_key
            current_model = key_manager.current_model

            client = genai.Client(api_key=current_key)
            full_prompt = f"{SQL_AGENT_PROMPT}\n\nUser question: {question}"

            logger.info(
                f"[SQLAgent] Attempt {attempt}: Generating SQL for: '{question}' | "
                f"Model: {current_model} | Key: ...{current_key[-6:]}"
            )

            response = await client.aio.models.generate_content(
                model=current_model,
                contents=full_prompt,
            )

            raw_sql = response.text.strip()

            # Clean up markdown code fences if Gemini wraps in ```sql ... ```
            if raw_sql.startswith("```"):
                lines = raw_sql.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                raw_sql = "\n".join(lines).strip()

            logger.info(f"[SQLAgent] Generated SQL: {raw_sql}")
            return raw_sql

        except Exception as e:
            last_exception = e
            if is_quota_error(e):
                logger.warning(
                    f"[SQLAgent] Attempt {attempt}: Quota error. Rotating... "
                    f"Error: {str(e)[:100]}"
                )
                key_manager.rotate()
                await asyncio.sleep(2)
            else:
                # Non-quota error — don't keep retrying indefinitely
                logger.error(f"[SQLAgent] Non-quota error: {e}")
                if attempt >= 3:
                    raise
                await asyncio.sleep(1)

    logger.error("[SQLAgent] All API key + model combinations exhausted!")
    raise last_exception
