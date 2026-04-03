from __future__ import annotations

from typing import Optional, Set

import psycopg
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash

from permissions import PERMS, DEFAULT_ROLES


def get_db(database_url: str):
    return psycopg.connect(database_url, row_factory=dict_row)


def init_db(database_url: str) -> None:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name VARCHAR(100),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS permissions (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_roles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, role_id)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id SERIAL PRIMARY KEY,
                    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(role_id, permission_id)
                );
                """
            )

        conn.commit()

    seed_rbac(database_url)
    seed_admin_user(database_url)


def seed_rbac(database_url: str) -> None:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            for code, desc in PERMS:
                cur.execute(
                    """
                    INSERT INTO permissions (code, description)
                    VALUES (%s, %s)
                    ON CONFLICT (code) DO UPDATE
                    SET description = EXCLUDED.description
                    """,
                    (code, desc),
                )

            for role_name, role_info in DEFAULT_ROLES.items():
                cur.execute(
                    """
                    INSERT INTO roles (name, description)
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET description = EXCLUDED.description
                    """,
                    (role_name, role_info["description"]),
                )

            for role_name, role_info in DEFAULT_ROLES.items():
                cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
                role_row = cur.fetchone()
                if not role_row:
                    continue

                role_id = role_row["id"]

                for perm_code in role_info["permissions"]:
                    cur.execute("SELECT id FROM permissions WHERE code = %s", (perm_code,))
                    perm_row = cur.fetchone()
                    if not perm_row:
                        continue

                    permission_id = perm_row["id"]

                    cur.execute(
                        """
                        INSERT INTO role_permissions (role_id, permission_id)
                        VALUES (%s, %s)
                        ON CONFLICT (role_id, permission_id) DO NOTHING
                        """,
                        (role_id, permission_id),
                    )

        conn.commit()


def seed_admin_user(database_url: str) -> None:
    import os

    admin_username = os.environ.get("CREATEX_INIT_ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("CREATEX_INIT_ADMIN_PASSWORD", "1234")
    admin_display_name = os.environ.get("CREATEX_INIT_ADMIN_DISPLAY_NAME", "劉建佑")

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (admin_username,))
            user = cur.fetchone()

            if not user:
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, display_name, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (
                        admin_username,
                        generate_password_hash(admin_password),
                        admin_display_name,
                    ),
                )
                user_id = cur.fetchone()["id"]
            else:
                user_id = user["id"]

            cur.execute("SELECT id FROM roles WHERE name = %s", ("Owner",))
            role = cur.fetchone()

            if role:
                cur.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """,
                    (user_id, role["id"]),
                )

        conn.commit()


def get_user_roles(database_url: str, user_id: int) -> list[str]:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    return [row["name"] for row in rows]


def get_user_permissions(database_url: str, user_id: int) -> Set[str]:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT p.code
                FROM user_roles ur
                JOIN role_permissions rp ON rp.role_id = ur.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = %s
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    return {row["code"] for row in rows}


def get_user_by_username(database_url: str, username: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, display_name, is_active
                FROM users
                WHERE username = %s
                """,
                (username,),
            )
            return cur.fetchone()


def get_user_by_id(database_url: str, user_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, display_name, is_active
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            return cur.fetchone()