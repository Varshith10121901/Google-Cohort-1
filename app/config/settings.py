# TASK: Project 1 (AURA Lite Core - Environment Config)
"""
settings.py
-----------
Centralized environment-based configuration for AURA Lite.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_api_keys: str = ""  # Comma-separated list of all API keys
    model_name: str = "gemini-2.5-flash-lite"
    fallback_model_name: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",   # silently ignore unknown env vars (e.g. GOOGLE_API_KEY)
    )

    def get_api_keys(self) -> list[str]:
        """Returns the list of all available API keys."""
        if self.gemini_api_keys:
            return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]
        if self.gemini_api_key:
            return [self.gemini_api_key]
        return []


settings = Settings()
