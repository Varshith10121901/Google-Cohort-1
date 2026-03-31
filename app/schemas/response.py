# TASK: Project 1 & 2 (AURA Lite - Response Schemas)
"""
response.py
-----------
Pydantic response schemas for /predict endpoints.
Project 1: PredictResponse (text summarization)
Project 2: CropResponse (crop recommendation)
"""

from pydantic import BaseModel
from typing import Literal, Optional


class PredictResponse(BaseModel):
    """Project 1: Text summarization response."""
    summary: str
    status: Literal["success", "error"]


class CropDetail(BaseModel):
    """Individual crop recommendation detail."""
    name: str
    profit_per_acre: int
    season: str
    description: str


class WeatherInfo(BaseModel):
    """Weather data returned in crop response."""
    location: str
    temperature: float
    feels_like: float
    rainfall: str
    humidity: int
    description: str


class CropResponse(BaseModel):
    """Project 2: Crop recommendation response."""
    location: str
    weather: Optional[WeatherInfo] = None
    recommended_crops: list[CropDetail]
    source: Literal["json", "ai", "none", "error"]
    reason: str
    status: Literal["success", "error"]


class QueryResponse(BaseModel):
    """Project 3: Database query response."""
    query: Optional[str] = None
    results: list = []
    total_results: int = 0
    status: Literal["success", "error"]
    error: Optional[str] = None
