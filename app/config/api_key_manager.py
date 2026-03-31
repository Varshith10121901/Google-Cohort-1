# TASK: AURA Lite - API Key Rotation & Model Fallback Manager
"""
api_key_manager.py
------------------
Centralized manager that handles:
1. Model fallback: gemini-2.5-flash-lite → gemini-2.5-flash
2. API key rotation: cycles through 10 keys when quota is hit
3. Guarantees a response — NEVER shows 429 to the user.
"""

import os
import asyncio
import threading
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class APIKeyManager:
    """Thread-safe singleton that manages API key rotation and model fallback."""

    def __init__(self):
        self._lock = threading.Lock()
        self._api_keys = settings.get_api_keys()
        self._current_key_index = 0
        self._models = [settings.model_name, settings.fallback_model_name]
        self._current_model_index = 0

        if not self._api_keys:
            logger.error("[APIKeyManager] No API keys configured! Check .env")
        else:
            logger.info(f"[APIKeyManager] Loaded {len(self._api_keys)} API keys.")
            logger.info(f"[APIKeyManager] Primary model: {self._models[0]}, Fallback: {self._models[1]}")
            # Set the initial key into the environment
            self._apply_current_key()

    @property
    def current_key(self) -> str:
        with self._lock:
            return self._api_keys[self._current_key_index] if self._api_keys else ""

    @property
    def current_model(self) -> str:
        with self._lock:
            return self._models[self._current_model_index]

    def _apply_current_key(self):
        """Push the current key into environment variables so all SDKs pick it up."""
        key = self._api_keys[self._current_key_index]
        os.environ["GOOGLE_API_KEY"] = key
        os.environ["GEMINI_API_KEY"] = key
        logger.info(
            f"[APIKeyManager] Active key: ...{key[-6:]} | "
            f"Model: {self._models[self._current_model_index]} | "
            f"Key slot: {self._current_key_index + 1}/{len(self._api_keys)}"
        )

    def rotate(self) -> bool:
        """
        Attempt to rotate to the next available configuration.
        Order: switch model first → then rotate key → repeat.
        Returns True if there are still combinations to try, False if all exhausted.
        """
        with self._lock:
            # Step 1: Try switching model (lite → full)
            if self._current_model_index < len(self._models) - 1:
                self._current_model_index += 1
                os.environ["MODEL_NAME"] = self._models[self._current_model_index]
                logger.warning(
                    f"[APIKeyManager] 429 hit → Switching model to: "
                    f"{self._models[self._current_model_index]}"
                )
                return True

            # Step 2: Model exhausted — rotate to next API key and reset model
            self._current_model_index = 0  # Reset back to lite model
            self._current_key_index = (self._current_key_index + 1) % len(self._api_keys)
            self._apply_current_key()
            os.environ["MODEL_NAME"] = self._models[self._current_model_index]
            logger.warning(
                f"[APIKeyManager] 429 hit → Rotated to key slot "
                f"{self._current_key_index + 1}/{len(self._api_keys)}, "
                f"model reset to {self._models[self._current_model_index]}"
            )
            return True

    def get_total_combinations(self) -> int:
        """Total number of key×model combinations available."""
        return len(self._api_keys) * len(self._models)


# Global singleton
key_manager = APIKeyManager()


def is_quota_error(exception: Exception) -> bool:
    """Check if an exception is a 429 RESOURCE_EXHAUSTED quota error."""
    err_str = str(exception).lower()
    return any(keyword in err_str for keyword in [
        "429",
        "resource_exhausted",
        "quota",
        "rate limit",
        "exceeded your current quota",
    ])


async def execute_with_fallback(async_fn, *args, **kwargs):
    """
    Wraps any async Gemini call with automatic model fallback + key rotation.
    Guarantees a response by cycling through all key×model combinations.
    
    Usage:
        result = await execute_with_fallback(some_async_gemini_call, prompt)
    """
    max_attempts = key_manager.get_total_combinations() + 2  # Extra buffer
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await async_fn(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if is_quota_error(e):
                logger.warning(
                    f"[Fallback] Attempt {attempt}: Quota error detected. "
                    f"Rotating... Error: {str(e)[:100]}"
                )
                key_manager.rotate()
                # Wait a moment before retrying to respect rate limits
                await asyncio.sleep(2)
            else:
                # Non-quota error — re-raise immediately
                raise

    # If we've exhausted everything, raise the last error
    logger.error("[Fallback] All API key + model combinations exhausted!")
    raise last_exception
