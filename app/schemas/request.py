# TASK: Project 1 & 2 (AURA Lite - Request Validation)
"""
request.py
----------
Pydantic request schemas for /predict endpoints.
Project 1: PredictRequest (text summarization)
Project 2: CropRequest (location-based crop suggestion)
"""

from pydantic import BaseModel, field_validator


class PredictRequest(BaseModel):
    """Project 1: Text summarization request."""
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Input text must not be empty.")
        if len(v) > 50_000:
            raise ValueError("Input text exceeds maximum allowed length of 50,000 characters.")
        return v


class CropRequest(BaseModel):
    """Project 2: Crop recommendation request."""
    location: str

    @field_validator("location")
    @classmethod
    def location_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Location must not be empty.")
        if len(v) > 200:
            raise ValueError("Location name is too long.")
        return v.strip()


class QueryRequest(BaseModel):
    """Project 3: Natural language database query request."""
    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question must not be empty.")
        if len(v) > 1000:
            raise ValueError("Question exceeds maximum allowed length of 1,000 characters.")
        return v.strip()
