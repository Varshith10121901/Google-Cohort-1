# TASK: Project 1 (AURA Lite Core - Agent Tools)
"""
tools.py
--------
ADK-compatible tools available to the AURA Lite agent.
"""

import re


def clean_text(text: str) -> str:
    """
    Clean and normalize input text before sending it to the model.

    Steps:
    - Strip leading/trailing whitespace
    - Collapse multiple spaces/newlines into a single space
    - Remove non-printable characters
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x20-\x7E\n]", "", text)
    return text
