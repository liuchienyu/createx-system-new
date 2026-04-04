from database import get_db


def list_job_titles(database_url: str, active_filter: str = ""):
    query = """
        SELECT id, name, level, sort_order, is_active
        FROM job_titles
    """
    params = []

    if active_filter == "true":
        query += " WHERE is_active = TRUE"
    elif active_filter == "false":
        query += " WHERE is_active = FALSE"

    query += " ORDER BY level ASC, sort_order ASC, id ASC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_job_title(database_url: str, title_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM job_titles WHERE id = %s", (title_id,))
            return cur.fetchone()


def create_job_title(database_url: str, name: str, level: int, sort_order: int, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO job_titles (name, level, sort_order, is_active)
                VALUES (%s, %s, %s, %s)
                """,
                (name, level, sort_order, is_active),
            )
        conn.commit()


def update_job_title(database_url: str, title_id: int, name: str, level: int, sort_order: int, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE job_titles
                SET name = %s,
                    level = %s,
                    sort_order = %s,
                    is_active = %s
                WHERE id = %s
                """,
                (name, level, sort_order, is_active, title_id),
            )
        conn.commit()


def disable_job_title(database_url: str, title_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE job_titles
                SET is_active = FALSE
                WHERE id = %s
                """,
                (title_id,),
            )
        conn.commit()


def active_employee_count_by_job_title(database_url: str, title_id: int) -> int:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM employees
                WHERE job_title_id = %s
                  AND status IN ('active', 'probation', 'leave')
                """,
                (title_id,),
            )
            return cur.fetchone()["cnt"]