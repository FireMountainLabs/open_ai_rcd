"""
Authentication decorators - No-op versions for customer deliverable.
Authentication has been removed from the customer deliverable.
"""

from functools import wraps


def create_auth_decorators(is_auth_enabled_func, get_current_user_func):
    """
    Create authentication decorators.
    In this customer deliverable, authentication is disabled, so these are no-ops.

    Args:
        is_auth_enabled_func: Function that returns whether auth is enabled (always False)
        get_current_user_func: Function that returns current user (not used)

    Returns:
        Tuple of (require_auth, require_admin) decorator functions
    """

    def require_auth(f):
        """
        Decorator that requires authentication.
        In customer deliverable, this is a no-op - all routes are accessible.
        """

        @wraps(f)
        def decorated_function(*args, **kwargs):
            # No authentication required - just call the function
            return f(*args, **kwargs)

        return decorated_function

    def require_admin(f):
        """
        Decorator that requires admin privileges.
        In customer deliverable, this is a no-op - all routes are accessible.
        """

        @wraps(f)
        def decorated_function(*args, **kwargs):
            # No admin check required - just call the function
            return f(*args, **kwargs)

        return decorated_function

    return require_auth, require_admin
