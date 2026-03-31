# TASK: Project 3 (AURA Lite - Query Engine)
"""
query_engine.py
---------------
Orchestrates the full NL → SQL → DB → Result pipeline.
1. Receives a natural language question
2. Calls Gemini via sql_agent to generate SQL
3. Validates the SQL (SELECT-only)
4. Executes on AlloyDB via db_connect
5. Returns structured output
"""

from app.agent.sql_agent import generate_sql_from_question
from app.db.db_connect import execute_query
from app.utils.logger import get_logger

logger = get_logger(__name__)


def validate_sql(sql: str) -> str:
    """
    Validates that the SQL is a safe SELECT query.
    Returns the cleaned SQL or raises ValueError.
    """
    cleaned = sql.strip().rstrip(";").strip()

    # Must start with SELECT (case-insensitive)
    if not cleaned.upper().startswith("SELECT"):
        raise ValueError(
            "Only SELECT queries are allowed. Received: "
            + cleaned[0:50] + "..."
        )

    # Block dangerous statements
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "EXEC", "GRANT", "REVOKE"]
    upper_sql = cleaned.upper()
    for keyword in forbidden:
        # Check for standalone keyword (not part of column names)
        if f" {keyword} " in f" {upper_sql} ":
            raise ValueError(f"Forbidden SQL keyword detected: {keyword}")

    # Re-add semicolon for execution
    return cleaned + ";"


async def run_query(question: str) -> dict:
    """
    End-to-end pipeline: natural language → SQL → database → results.
    Returns a structured dict with query, results, and status.
    """
    try:
        # Step 1: Generate SQL from the question
        raw_sql = await generate_sql_from_question(question)

        # Step 2: Validate the SQL
        safe_sql = validate_sql(raw_sql)

        # Step 3: Execute on the database
        result = execute_query(safe_sql)

        # Step 4: Format results
        rows = result.get("rows", [])

        # Flatten to a simple list if single-column result
        if rows and len(rows[0]) == 1:
            key = list(rows[0].keys())[0]
            flat_results = [row[key] for row in rows]
        else:
            flat_results = rows

        return {
            "query": safe_sql,
            "results": flat_results,
            "total_results": len(flat_results),
            "status": "success",
        }

    except ValueError as e:
        logger.warning(f"[QueryEngine] Validation error: {e}")
        return {
            "query": None,
            "results": [],
            "total_results": 0,
            "status": "error",
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"[QueryEngine] Execution error: {e}")
        return {
            "query": None,
            "results": [],
            "total_results": 0,
            "status": "error",
            "error": f"Database query failed: {str(e)}",
        }
