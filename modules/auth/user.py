from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, username, display_name, is_active=True, roles=None, permissions=None):
        self.id = str(user_id)
        self.username = username
        self.display_name = display_name or username
        self.active = is_active
        self.roles = roles or []
        self.permissions = permissions or set()

    @property
    def is_active(self):
        return self.active

    def has_permission(self, perm_code: str) -> bool:
        return perm_code in self.permissions