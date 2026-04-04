from database import get_db


def get_finance_categories(database_url: str, category_type: str | None = None, active_filter: str = "true"):
    query = """
        SELECT id, category_type, name, sort_order, is_active
        FROM finance_categories
    """
    conditions = []
    params = []

    if active_filter == "true":
        conditions.append("is_active = TRUE")
    elif active_filter == "false":
        conditions.append("is_active = FALSE")

    if category_type:
        conditions.append("category_type = %s")
        params.append(category_type)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY category_type ASC, sort_order ASC, id ASC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_finance_category(database_url: str, category_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, category_type, name, sort_order, is_active
                FROM finance_categories
                WHERE id = %s
                """,
                (category_id,),
            )
            return cur.fetchone()


def create_finance_category(database_url: str, category_type: str, name: str, sort_order: int, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO finance_categories (category_type, name, sort_order, is_active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (category_type, name) DO NOTHING
                """,
                (category_type, name, sort_order, is_active),
            )
        conn.commit()


def update_finance_category(database_url: str, category_id: int, category_type: str, name: str, sort_order: int, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE finance_categories
                SET category_type = %s,
                    name = %s,
                    sort_order = %s,
                    is_active = %s
                WHERE id = %s
                """,
                (category_type, name, sort_order, is_active, category_id),
            )
        conn.commit()

def disable_finance_category(database_url: str, category_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE finance_categories
                SET is_active = FALSE
                WHERE id = %s
                """,
                (category_id,),
            )
        conn.commit()