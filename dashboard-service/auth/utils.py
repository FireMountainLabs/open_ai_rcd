"""
Authentication utilities - No-op versions for customer deliverable.
Authentication has been removed from the customer deliverable.
"""

from typing import Optional, Dict, Any


def get_current_user(auth_service_url: str = None, is_auth_enabled: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get current user from session or token.
    In customer deliverable, authentication is disabled, so this always returns None.

    Args:
        auth_service_url: URL of auth service (not used)
        is_auth_enabled: Whether auth is enabled (always False)

    Returns:
        None (no authentication in customer deliverable)
    """
    return None
