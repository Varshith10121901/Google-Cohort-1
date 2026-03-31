# TASK: Project 3 (AURA Lite - AlloyDB Connection)
"""
db_connect.py
-------------
Reusable PostgreSQL/AlloyDB connection helper using psycopg2.
Reads credentials from environment variables.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_db_connection():
    """
    Creates and returns a new psycopg2 connection to AlloyDB/PostgreSQL.
    Uses environment variables: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            dbname=os.getenv("DB_NAME", "aura_lite"),
            port=int(os.getenv("DB_PORT", "5432")),
        )
        logger.info("[DB] Connection established successfully.")
        return conn
    except psycopg2.Error as e:
        logger.error(f"[DB] Connection failed: {e}")
        raise


def init_db():
    """
    Initializes the crops table if it does not already exist.
    Called once at application startup.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS crops (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        min_temp INT,
        max_temp INT,
        rainfall TEXT,
        season TEXT,
        soil_type TEXT,
        water_requirement TEXT,
        profit_level TEXT
    );
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
        conn.commit()
        logger.info("[DB] Table 'crops' ensured to exist.")
    except psycopg2.Error as e:
        logger.error(f"[DB] init_db failed: {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_query(sql: str):
    """
    Executes a read-only SQL query and returns the results as a list of dicts.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return {"columns": columns, "rows": [dict(row) for row in rows]}
    except psycopg2.Error as e:
        logger.error(f"[DB] Query execution failed: {e}")
        raise
    finally:
        if conn:
            conn.close()
