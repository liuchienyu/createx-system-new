from werkzeug.security import generate_password_hash

from database import get_db


def list_users(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, display_name, is_active, created_at
                FROM users
                ORDER BY id ASC
                """
            )
            return cur.fetchall()


def get_user(database_url: str, user_id: int):
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


def create_user(database_url: str, username: str, display_name: str, password: str, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            exists = cur.fetchone()
            if exists:
                return False, "此帳號已存在", None

            cur.execute(
                """
                INSERT INTO users (username, password_hash, display_name, is_active)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    username,
                    generate_password_hash(password),
                    display_name or username,
                    is_active,
                ),
            )
            user_id = cur.fetchone()["id"]
        conn.commit()

    return True, "使用者建立成功", user_id


def update_user(database_url: str, user_id: int, display_name: str, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET display_name = %s,
                    is_active = %s
                WHERE id = %s
                """,
                (display_name, is_active, user_id),
            )
        conn.commit()


def update_user_with_password(database_url: str, user_id: int, display_name: str, password: str, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET display_name = %s,
                    password_hash = %s,
                    is_active = %s
                WHERE id = %s
                """,
                (
                    display_name,
                    generate_password_hash(password),
                    is_active,
                    user_id,
                ),
            )
        conn.commit()


def reset_user_password(database_url: str, user_id: int, new_password: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (generate_password_hash(new_password), user_id),
            )
        conn.commit()


def delete_user(database_url: str, user_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()


def list_roles(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, description
                FROM roles
                ORDER BY id ASC
                """
            )
            return cur.fetchall()


def get_user_role_ids(database_url: str, user_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role_id
                FROM user_roles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    return {row["role_id"] for row in rows}


def assign_user_roles(database_url: str, user_id: int, role_ids: list[int]):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))

            for role_id in role_ids:
                cur.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """,
                    (user_id, role_id),
                )
        conn.commit()


def owner_count(database_url: str) -> int:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE r.name = 'Owner'
                """
            )
            return cur.fetchone()["cnt"]


def is_owner_user(database_url: str, user_id: int) -> bool:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s AND r.name = 'Owner'
                """,
                (user_id,),
            )
            return cur.fetchone()["cnt"] > 0