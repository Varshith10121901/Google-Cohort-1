# TASK: Project 2 (AURA Lite MCP - JSON Crop Recommendation Engine)
"""
crop_tool.py
------------
Loads crop_data.json and filters crops based on temperature and rainfall.
Returns top 3 crops sorted by profit per acre.
This is the PRIMARY (rule-based) recommendation engine.
"""

import json
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Resolve path relative to project root
DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "data", "crop_data.json"
)


FAMOUS_CROPS_BY_STATE = [
    { "state": "Andhra Pradesh", "famous_crop": "Chillies", "other_major_crops": ["Rice", "Tobacco", "Cotton"] },
    { "state": "Arunachal Pradesh", "famous_crop": "Oranges", "other_major_crops": ["Maize", "Millet", "Rice"] },
    { "state": "Assam", "famous_crop": "Tea", "other_major_crops": ["Jute", "Rice", "Bamboos"] },
    { "state": "Bihar", "famous_crop": "Litchi", "other_major_crops": ["Maize", "Rice", "Wheat"] },
    { "state": "Chhattisgarh", "famous_crop": "Rice (Paddy)", "other_major_crops": ["Maize", "Pulses", "Nigerseed"] },
    { "state": "Goa", "famous_crop": "Cashew", "other_major_crops": ["Coconut", "Rice", "Feni"] },
    { "state": "Gujarat", "famous_crop": "Cotton", "other_major_crops": ["Groundnut", "Dates", "Sugarcane"] },
    { "state": "Haryana", "famous_crop": "Basmati Rice", "other_major_crops": ["Wheat", "Sugarcane", "Mustard"] },
    { "state": "Himachal Pradesh", "famous_crop": "Apples", "other_major_crops": ["Maize", "Barley", "Kangra Tea"] },
    { "state": "Jharkhand", "famous_crop": "Rice", "other_major_crops": ["Maize", "Pulses", "Oilseeds"] },
    { "state": "Karnataka", "famous_crop": "Coffee", "other_major_crops": ["Ragi", "Sugarcane", "Areca Nut"] },
    { "state": "Kerala", "famous_crop": "Rubber", "other_major_crops": ["Spices (Pepper/Cardamom)", "Coconut", "Banana"] },
    { "state": "Madhya Pradesh", "famous_crop": "Soybean", "other_major_crops": ["Wheat", "Gram", "Garlic"] },
    { "state": "Maharashtra", "famous_crop": "Sugarcane", "other_major_crops": ["Grapes", "Cotton", "Jowar"] },
    { "state": "Manipur", "famous_crop": "Black Rice (Chak-Hao)", "other_major_crops": ["Maize", "Pineapple", "Citrus"] },
    { "state": "Meghalaya", "famous_crop": "Lakadong Turmeric", "other_major_crops": ["Khasi Mandarin", "Pineapple", "Rice"] },
    { "state": "Mizoram", "famous_crop": "Ginger", "other_major_crops": ["Bamboo Shoots", "Mizo Chilli", "Rice"] },
    { "state": "Nagaland", "famous_crop": "Naga King Chilli", "other_major_crops": ["Maize", "Tree Tomato", "Naga Cucumber"] },
    { "state": "Odisha", "famous_crop": "Rice", "other_major_crops": ["Turmeric (Kandhamal)", "Oilseeds", "Jute"] },
    { "state": "Punjab", "famous_crop": "Wheat", "other_major_crops": ["Rice", "Cotton", "Sugarcane"] },
    { "state": "Rajasthan", "famous_crop": "Bajra (Pearl Millet)", "other_major_crops": ["Mustard", "Guar Seed", "Wheat"] },
    { "state": "Sikkim", "famous_crop": "Large Cardamom", "other_major_crops": ["Ginger", "Buckwheat", "Mandarin Orange"] },
    { "state": "Tamil Nadu", "famous_crop": "Bananas", "other_major_crops": ["Coconut", "Sugarcane", "Turmeric"] },
    { "state": "Telangana", "famous_crop": "Cotton", "other_major_crops": ["Rice", "Maize", "Red Gram"] },
    { "state": "Tripura", "famous_crop": "Queen Pineapple", "other_major_crops": ["Rubber", "Rice", "Tea"] },
    { "state": "Uttar Pradesh", "famous_crop": "Sugarcane", "other_major_crops": ["Wheat", "Potato", "Mango"] },
    { "state": "Uttarakhand", "famous_crop": "Basmati Rice", "other_major_crops": ["Wheat", "Mandua (Finger Millet)", "Soybean"] },
    { "state": "West Bengal", "famous_crop": "Jute", "other_major_crops": ["Rice", "Darjeeling Tea", "Potato"] }
]


def _load_crop_data() -> list:
    """Load crop dataset from JSON file."""
    resolved = os.path.normpath(DATA_PATH)
    logger.info(f"[CropTool] Loading crop data from: {resolved}")
    with open(resolved, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("crops", [])


def get_crop_from_json(location: str, temperature: float, rainfall: str) -> dict:
    """
    Filter crops by temperature range and rainfall level.
    Returns top 3 crops sorted by profit_per_acre (descending).

    Args:
        temperature: Current temperature in Celsius.
        rainfall: "low", "medium", or "high".

    Returns:
        {
            "recommended_crops": [
                {
                    "name": str,
                    "profit_per_acre": int,
                    "season": str,
                    "description": str
                }
            ],
            "source": "json",
            "match_count": int
        }
    """
    crops = _load_crop_data()
    rainfall_lower = rainfall.lower()

    matched = []
    for crop in crops:
        temp_match = crop["min_temp"] <= temperature <= crop["max_temp"]
        rain_match = crop["rainfall"] == rainfall_lower
        if temp_match and rain_match:
            matched.append(crop)

    # Sort by profit descending
    matched.sort(key=lambda c: c["profit_per_acre"], reverse=True)

    # Determine if the user queried specifically for a State (and not a district)
    # The weather API returns format like: "Pune, Maharashtra, India" or "Maharashtra, Maharashtra, India"
    # If the first part (city/district) matches the second part (state), or if they literally just typed the state
    loc_parts = [p.strip().lower() for p in location.split(',')]
    city_or_query = loc_parts[0] if loc_parts else ""

    state_match = None
    for region_data in FAMOUS_CROPS_BY_STATE:
        state_name = region_data["state"].lower()
        if city_or_query == state_name:
            state_match = region_data
            break

    final_crops = []

    if state_match:
        logger.info(f"[CropTool] State match detected for: {state_match['state']}")
        
        # Pull out the famous crop and other major crops from the existing dataset to keep full details
        famous_names = [state_match["famous_crop"].lower()] + [c.lower() for c in state_match["other_major_crops"]]
        
        # Find them in our dataset (regardless of temp/rainfall, since they are historically famous there)
        priority_crops = []
        for c in crops:
            if c["name"].lower() in famous_names or any(fname in c["name"].lower() for fname in famous_names):
                priority_crops.append(c)
                
        # Fill the first spots with the state's famous crops
        for c in priority_crops:
            if c not in final_crops:
                final_crops.append(c)

        # Pad the rest with temperature-based crops
        for c in matched:
            if c not in final_crops:
                final_crops.append(c)
                
        # Limit to top 3
        top_crops = final_crops[:3]
    else:
        logger.info("[CropTool] District/City-level query detected, applying pure temperature/rainfall match.")
        top_crops = matched[:3]

    result = {
        "recommended_crops": [
            {
                "name": c["name"],
                "profit_per_acre": c["profit_per_acre"],
                "season": c["season"],
                "description": c["description"],
            }
            for c in top_crops
        ],
        "source": "json",
        "match_count": len(matched),
    }

    logger.info(f"[CropTool] Found {len(matched)} matches, returning top {len(top_crops)}")
    return result
