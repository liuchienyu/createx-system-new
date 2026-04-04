from database import get_db


def parse_month_filter(month_str: str):
    if not month_str:
        return None, None

    try:
        year, month = month_str.split("-")
        year = int(year)
        month = int(month)

        start_date = f"{year:04d}-{month:02d}-01"

        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"

        return start_date, end_date
    except Exception:
        return None, None


def list_finance_records(database_url: str, month: str = ""):
    start_date, end_date = parse_month_filter(month)

    query = """
        SELECT fr.id,
               fr.record_date,
               fr.category_type,
               fr.category_name,
               fr.item_name,
               fr.amount,
               fr.payment_method,
               fr.counterparty,
               fr.note,
               fr.created_at,
               p.name AS project_name,
               u.display_name AS created_by_name
        FROM finance_records fr
        LEFT JOIN users u ON u.id = fr.created_by
        LEFT JOIN projects p ON p.id = fr.project_id
    """
    params = []

    if start_date and end_date:
        query += " WHERE fr.record_date >= %s AND fr.record_date < %s"
        params.extend([start_date, end_date])

    query += " ORDER BY fr.record_date DESC, fr.id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall(), start_date, end_date


def get_finance_record(database_url: str, record_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM finance_records
                WHERE id = %s
                """,
                (record_id,),
            )
            return cur.fetchone()


def create_finance_record(
    database_url: str,
    record_date: str,
    category_type: str,
    category_id: int,
    category_name: str,
    item_name: str,
    amount: float,
    payment_method: str,
    counterparty: str,
    note: str,
    created_by: int,
    project_id: int | None,
):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO finance_records (
                    record_date, category_type, category_id, category_name, item_name,
                    amount, payment_method, counterparty, note, created_by, project_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record_date,
                    category_type,
                    category_id,
                    category_name,
                    item_name,
                    amount,
                    payment_method,
                    counterparty,
                    note,
                    created_by,
                    project_id,
                ),
            )
        conn.commit()


def update_finance_record(
    database_url: str,
    record_id: int,
    record_date: str,
    category_type: str,
    category_id: int,
    category_name: str,
    item_name: str,
    amount: float,
    payment_method: str,
    counterparty: str,
    note: str,
    project_id: int | None,
):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE finance_records
                SET record_date = %s,
                    category_type = %s,
                    category_id = %s,
                    category_name = %s,
                    item_name = %s,
                    amount = %s,
                    payment_method = %s,
                    counterparty = %s,
                    note = %s,
                    project_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    record_date,
                    category_type,
                    category_id,
                    category_name,
                    item_name,
                    amount,
                    payment_method,
                    counterparty,
                    note,
                    project_id,
                    record_id,
                ),
            )
        conn.commit()


def delete_finance_record(database_url: str, record_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM finance_records WHERE id = %s", (record_id,))
        conn.commit()


def list_projects_for_select(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name
                FROM projects
                WHERE is_active = TRUE
                ORDER BY id DESC
                """
            )
            return cur.fetchall()