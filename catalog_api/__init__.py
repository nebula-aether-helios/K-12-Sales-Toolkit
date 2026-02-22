"""Catalog API package

Expose a lightweight AI client and settings so other modules can import them easily.
"""
from . import config
from .ai_client import ai_chat

# convenience exports
settings = config.settings
__all__ = ["ai_chat", "settings"]
