"""Identifier helpers for generating short external IDs."""
from __future__ import annotations

import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits
HUB_CODE_PREFIX = "HUB-"
DEFAULT_CODE_LENGTH = 8


def generate_hub_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generate a random hub code with a fixed prefix."""

    token = "".join(secrets.choice(ALPHABET) for _ in range(max(4, length)))
    return f"{HUB_CODE_PREFIX}{token}"
