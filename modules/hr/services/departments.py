from database import get_db


def list_departments(database_url: str, only_active: bool = False):
    query = """
        SELECT d.id, d.name, d.parent_id, d.sort_order, d.is_active,
               p.name AS parent_name
        FROM departments d
        LEFT JOIN departments p ON p.id = d.parent_id
    """
    if only_active:
        query += " WHERE d.is_active = TRUE"
    query += " ORDER BY d.sort_order ASC, d.id ASC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def get_department(database_url: str, department_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM departments WHERE id = %s", (department_id,))
            return cur.fetchone()


def create_department(database_url: str, name: str, parent_id: int | None, sort_order: int, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO departments (name, parent_id, sort_order, is_active)
                VALUES (%s, %s, %s, %s)
                """,
                (name, parent_id, sort_order, is_active),
            )
        conn.commit()


def update_department(database_url: str, department_id: int, name: str, parent_id: int | None, sort_order: int, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE departments
                SET name = %s,
                    parent_id = %s,
                    sort_order = %s,
                    is_active = %s
                WHERE id = %s
                """,
                (name, parent_id, sort_order, is_active, department_id),
            )
        conn.commit()


def disable_department(database_url: str, department_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE departments
                SET is_active = FALSE
                WHERE id = %s
                """,
                (department_id,),
            )
        conn.commit()


def active_employee_count_by_department(database_url: str, department_id: int) -> int:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM employees
                WHERE department_id = %s
                  AND status IN ('active', 'probation', 'leave')
                """,
                (department_id,),
            )
            return cur.fetchone()["cnt"]