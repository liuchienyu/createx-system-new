from functools import wraps

from flask import abort
from flask_login import current_user
from extensions import login_manager


def has_permission(user, perm_code: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return perm_code in getattr(user, "permissions", set())


def permission_required(perm_code: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()

            if not has_permission(current_user, perm_code):
                abort(403)

            return view_func(*args, **kwargs)

        return wrapped

    return decorator