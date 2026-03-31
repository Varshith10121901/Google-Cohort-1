# TASK: Project 3 (AURA Lite - Database Seeder)
"""
seed.py
-------
Reads crop_data.json and populates the crops table.
Maps JSON fields to the DB schema, deriving soil_type, water_requirement,
and profit_level from the original dataset.
"""

import json
import os
from app.db.db_connect import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Profit level classification based on profit_per_acre
PROFIT_THRESHOLDS = {"low": 40000, "medium": 80000}

# Derive water requirement from rainfall
WATER_MAP = {"low": "low", "medium": "moderate", "high": "high"}

# Default soil type mapping by crop characteristics
SOIL_DEFAULTS = {
    # 🌾 Cereals
    "Rice (Paddy)": "clayey",
    "Wheat": "loamy",
    "Maize (Corn)": "loamy",
    "Barley": "loamy",
    "Sorghum (Jowar)": "sandy loam",
    "Millet (Bajra)": "sandy",
    "Ragi (Finger Millet)": "red loamy",

    # 🌿 Pulses
    "Chickpea (Gram)": "sandy loam",
    "Pigeon Pea (Tur)": "loamy",
    "Lentil (Masoor)": "loamy",
    "Green Gram (Moong)": "sandy loam",
    "Black Gram (Urad)": "clayey loam",

    # 🌻 Oilseeds
    "Mustard": "loamy",
    "Groundnut (Peanut)": "sandy loam",
    "Soybean": "loamy",
    "Sunflower": "loamy",
    "Sesame (Til)": "sandy loam",
    "Castor": "sandy loam",

    # 🌱 Cash Crops
    "Sugarcane": "loamy",
    "Cotton": "black soil",
    "Jute": "alluvial",
    "Tobacco": "sandy loam",
    "Rubber": "laterite",
    "Coffee": "well-drained loamy",
    "Tea": "acidic loamy",

    # 🍌 Fruits
    "Banana": "loamy",
    "Mango": "well-drained loamy",
    "Orange": "sandy loam",
    "Apple": "loamy",
    "Grapes": "sandy loam",
    "Pineapple": "sandy loam",
    "Papaya": "well-drained loamy",
    "Guava": "loamy",
    "Coconut": "sandy loam",

    # 🥦 Vegetables
    "Tomato": "loamy",
    "Onion": "sandy loam",
    "Potato": "sandy loam",
    "Cabbage": "loamy",
    "Cauliflower": "loamy",
    "Brinjal (Eggplant)": "sandy loam",
    "Carrot": "sandy loam",
    "Radish": "sandy loam",
    "Spinach": "loamy",
    "Okra (Lady Finger)": "loamy",

    # 🌿 Spices & Plantation
    "Turmeric": "loamy",
    "Ginger": "loamy",
    "Cardamom": "well-drained loamy",
    "Black Pepper": "laterite",
    "Clove": "loamy",

    # 🌾 Fodder Crops
    "Napier Grass": "loamy",
    "Berseem": "clayey loam",
    "Lucerne (Alfalfa)": "well-drained loamy"
}


def _classify_profit(profit_per_acre: int) -> str:
    if profit_per_acre < PROFIT_THRESHOLDS["low"]:
        return "low"
    elif profit_per_acre < PROFIT_THRESHOLDS["medium"]:
        return "medium"
    else:
        return "high"


def seed_crops():
    """
    Reads data/crop_data.json and inserts rows into the crops table.
    Skips seeding if the table already has data.
    """
    # Resolve the JSON path relative to the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_path = os.path.join(base_dir, "data", "crop_data.json")

    if not os.path.exists(json_path):
        logger.warning(f"[Seed] crop_data.json not found at {json_path}. Skipping seed.")
        return

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if already seeded
            cur.execute("SELECT COUNT(*) FROM crops;")
            count = cur.fetchone()[0]
            if count > 0:
                logger.info(f"[Seed] Table 'crops' already has {count} rows. Skipping seed.")
                return

            # Load JSON
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            crops = data.get("crops", [])
            if not crops:
                logger.warning("[Seed] No crop data found in JSON.")
                return

            insert_sql = """
                INSERT INTO crops (name, min_temp, max_temp, rainfall, season, soil_type, water_requirement, profit_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """

            for crop in crops:
                name = crop["name"]
                min_temp = crop.get("min_temp", 0)
                max_temp = crop.get("max_temp", 0)
                rainfall = crop.get("rainfall", "medium")
                season = crop.get("season", "Unknown")
                soil_type = SOIL_DEFAULTS.get(name, "loamy")
                water_requirement = WATER_MAP.get(rainfall, "moderate")
                profit_level = _classify_profit(crop.get("profit_per_acre", 0))

                cur.execute(insert_sql, (
                    name, min_temp, max_temp, rainfall,
                    season, soil_type, water_requirement, profit_level,
                ))

            conn.commit()
            logger.info(f"[Seed] Successfully inserted {len(crops)} crops into the database.")

    except Exception as e:
        logger.error(f"[Seed] Seeding failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
