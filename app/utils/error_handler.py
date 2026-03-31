# TASK: Project 1 (AURA Lite Core - Error Handling)
"""
error_handler.py
----------------
Centralized exception logging utility.
"""

import logging
import traceback


def handle_exception(logger: logging.Logger, exc: Exception) -> None:
    """Log exception details with traceback."""
    logger.error(f"Exception occurred: {type(exc).__name__}: {exc}")
    logger.debug(traceback.format_exc())
