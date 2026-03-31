# TASK: Project 1 & 2 (AURA Lite - Inference Orchestrator)
"""
inference_service.py
--------------------
Orchestrates fully async ADK execution runs with automatic
API key rotation and model fallback on 429 errors.
"""

import asyncio
import os
import uuid
import json
import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from app.agent.core_agent import build_summarizer_agent, build_farmer_agent
from app.agent.tools import clean_text
from app.config.settings import settings
from app.config.api_key_manager import key_manager, is_quota_error
from app.utils.logger import get_logger

logger = get_logger(__name__)


class InferenceService:
    def __init__(self):
        if settings.gemini_api_key:
            os.environ.setdefault("GOOGLE_API_KEY", settings.gemini_api_key)

        self._session_service = InMemorySessionService()
        self._build_runners()

    def _build_runners(self):
        """Build/rebuild all ADK runners with the current model from key_manager."""
        # Project 1 Runner
        self._summarizer_agent = build_summarizer_agent()
        self._summarizer_runner = Runner(
            agent=self._summarizer_agent,
            app_name="aura_lite",
            session_service=self._session_service,
        )

        # Project 2 Runner (MCP Hybrid Farmer)
        self._farmer_agent = build_farmer_agent()
        self._farmer_runner = Runner(
            agent=self._farmer_agent,
            app_name="aura_farmer",
            session_service=self._session_service,
        )
        logger.info(
            f"[InferenceService] Runners built with model: {key_manager.current_model}, "
            f"key: ...{key_manager.current_key[-6:]}"
        )

    def _rebuild_after_rotation(self):
        """Rebuild runners after an API key or model rotation."""
        logger.info("[InferenceService] Rebuilding runners after key/model rotation...")
        self._build_runners()

    # ── PROJECT 1: SUMMARIZER ──────────────────────────────────────────────────
    async def summarize(self, raw_text: str) -> str:
        cleaned = clean_text(raw_text)
        logger.info(f"[InferenceService] Cleaned text length: {len(cleaned)} chars")

        max_rotations = key_manager.get_total_combinations() + 2
        last_exc: Exception = RuntimeError("Unknown error")

        for attempt in range(1, max_rotations + 1):
            try:
                logger.info(f"[InferenceService] Summarizer attempt {attempt}.")
                return await self._run_async(self._summarizer_runner, cleaned)
            except Exception as e:
                last_exc = e
                if is_quota_error(e):
                    logger.warning(
                        f"[InferenceService] Summarizer attempt {attempt} hit quota. Rotating..."
                    )
                    key_manager.rotate()
                    self._rebuild_after_rotation()
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"[InferenceService] Summarizer attempt {attempt} failed: {e}")
                    # Non-quota error: retry a couple times then fail
                    if attempt >= 3:
                        break
                    await asyncio.sleep(1)

        logger.error("[InferenceService] All summarizer attempts exhausted.")
        raise last_exc

    # ── PROJECT 2: CROP SUGGESTER ──────────────────────────────────────────────
    async def _verify_location(self, location: str) -> dict:
        """Pre-flight check using Gemini to determine if a location is suitable for farming."""
        from google import genai
        from app.config.api_key_manager import execute_with_fallback
        
        async def _call_gemini():
            client = genai.Client(api_key=key_manager.current_key)
            model_name = key_manager.current_model
            prompt = f"""Evaluate if '{location}' is a real, geographically valid, and physically suitable location for outdoor agriculture. 
            If it is a fictional place, an ocean, space, an active volcano, Antarctica, etc., it is NOT suitable.
            Reply strictly with JSON matching this exactly:
            {{"suitable": true, "reason": ""}} OR {{"suitable": false, "reason": "Detailed explanation of why it is not suitable."}}"""
            
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                if text.endswith("```"):
                    text = text[:-3]
            
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if not match:
                raise ValueError("No JSON returned from pre-flight check.")
            return json.loads(match.group(0))

        return await execute_with_fallback(_call_gemini)

    async def suggest_crop(self, location: str) -> dict:
        """Runs the Farmer Agent with automatic key rotation on 429 errors."""
        # --- Pre-flight location check ---
        try:
            logger.info(f"[InferenceService] Running pre-flight suitability check for '{location}'")
            pre_flight = await self._verify_location(location)
            if not pre_flight.get("suitable", True):
                logger.info(f"[InferenceService] Pre-flight rejected '{location}': {pre_flight.get('reason')}")
                return {
                    "location": location,
                    "recommended_crops": [],
                    "source": "none",
                    "reason": pre_flight.get("reason", "This location is not suitable for cultivation."),
                    "status": "success"
                }
        except Exception as e:
            logger.warning(f"[InferenceService] Pre-flight check failed: {e}. Proceeding to main agent.")

        max_rotations = key_manager.get_total_combinations() + 2
        last_exc: Exception = RuntimeError("Unknown error")

        for attempt in range(1, max_rotations + 1):
            try:
                logger.info(f"[InferenceService] Crop Suggest attempt {attempt} for '{location}'.")

                prompt = f"Target location: {location}"
                raw_response = await self._run_async(self._farmer_runner, prompt)

                # Robustly extract JSON using regex, ignoring any conversational fluff
                text = raw_response.strip()

                # Clean up markdown if it exists
                if text.startswith("```"):
                    text = text.split("\n", 1)[-1]
                    if text.endswith("```"):
                        text = text[:-3]

                # Extract just the JSON object from the response
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    text = match.group(0)
                else:
                    raise ValueError(f"No JSON object found in response: {raw_response[:100]}")

                return json.loads(text)

            except json.JSONDecodeError as e:
                last_exc = e
                logger.warning(f"[InferenceService] Crop Suggest failed to decode JSON: {e}")
                if attempt >= 3:
                    break
                await asyncio.sleep(1)
            except Exception as e:
                last_exc = e
                if is_quota_error(e):
                    logger.warning(
                        f"[InferenceService] Crop Suggest attempt {attempt} hit quota. Rotating..."
                    )
                    key_manager.rotate()
                    self._rebuild_after_rotation()
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"[InferenceService] Crop Suggest attempt {attempt} failed: {e}")
                    if attempt >= 3:
                        break
                    await asyncio.sleep(1)

        logger.error("[InferenceService] All crop suggest attempts exhausted.")
        raise last_exc

    # ── CORE ASYNC EXECUTION ───────────────────────────────────────────────────
    async def _run_async(self, runner: Runner, text: str) -> str:
        """Fully async core runner executor."""
        session_id = str(uuid.uuid4())
        user_id = "system"

        await self._session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )

        user_message = Content(role="user", parts=[Part(text=text)])
        final_text = ""

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text

        if not final_text:
            raise RuntimeError("Agent returned empty response.")

        return final_text
