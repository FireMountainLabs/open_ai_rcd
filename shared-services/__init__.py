"""
Shared services package for microservices.

Contains common service classes and utilities that can be used across
multiple microservices in the platform.
"""

from .invite_service import InviteService
from .common_config import common_config, CommonConfigManager

__all__ = ["InviteService", "common_config", "CommonConfigManager"]
