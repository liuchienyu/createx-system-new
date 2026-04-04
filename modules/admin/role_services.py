from database import get_db


def list_roles_with_permission_count(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.id, r.name, r.description,
                       COUNT(DISTINCT rp.permission_id) AS permission_count
                FROM roles r
                LEFT JOIN role_permissions rp ON rp.role_id = r.id
                GROUP BY r.id
                ORDER BY r.id ASC
                """
            )
            return cur.fetchall()


def get_role(database_url: str, role_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, description
                FROM roles
                WHERE id = %s
                """,
                (role_id,),
            )
            return cur.fetchone()


def get_all_permissions(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, code, description
                FROM permissions
                ORDER BY code ASC
                """
            )
            return cur.fetchall()


def get_role_permission_ids(database_url: str, role_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT permission_id
                FROM role_permissions
                WHERE role_id = %s
                """,
                (role_id,),
            )
            rows = cur.fetchall()

    return {row["permission_id"] for row in rows}


def create_role(database_url: str, name: str, description: str, permission_ids: list[int]):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE name = %s", (name,))
            exists = cur.fetchone()
            if exists:
                return False, "角色名稱已存在"

            cur.execute(
                """
                INSERT INTO roles (name, description)
                VALUES (%s, %s)
                RETURNING id
                """,
                (name, description),
            )
            role_id = cur.fetchone()["id"]

            for permission_id in permission_ids:
                cur.execute(
                    """
                    INSERT INTO role_permissions (role_id, permission_id)
                    VALUES (%s, %s)
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                    """,
                    (role_id, permission_id),
                )
        conn.commit()

    return True, "角色建立成功"


def update_role(database_url: str, role_id: int, name: str, description: str, permission_ids: list[int]):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM roles
                WHERE name = %s AND id <> %s
                """,
                (name, role_id),
            )
            exists = cur.fetchone()
            if exists:
                return False, "角色名稱已被使用"

            cur.execute(
                """
                UPDATE roles
                SET name = %s,
                    description = %s
                WHERE id = %s
                """,
                (name, description, role_id),
            )

            cur.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))

            for permission_id in permission_ids:
                cur.execute(
                    """
                    INSERT INTO role_permissions (role_id, permission_id)
                    VALUES (%s, %s)
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                    """,
                    (role_id, permission_id),
                )

        conn.commit()

    return True, "角色更新成功"