from database import get_db


def list_projects(database_url: str, is_active: str = ""):
    query = """
        SELECT id, name, description, start_date, end_date, is_active, created_at
        FROM projects
    """
    params = []

    if is_active == "true":
        query += " WHERE is_active = TRUE"
    elif is_active == "false":
        query += " WHERE is_active = FALSE"

    query += " ORDER BY id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_project(database_url: str, project_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, description, start_date, end_date, is_active, created_at
                FROM projects
                WHERE id = %s
                """,
                (project_id,),
            )
            return cur.fetchone()


def create_project(
    database_url: str,
    name: str,
    description: str,
    start_date: str | None,
    end_date: str | None,
    is_active: bool,
):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (name, description, start_date, end_date, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (name, description, start_date, end_date, is_active),
            )
            project_id = cur.fetchone()["id"]
        conn.commit()

    return project_id


def update_project(
    database_url: str,
    project_id: int,
    name: str,
    description: str,
    start_date: str | None,
    end_date: str | None,
    is_active: bool,
):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE projects
                SET name = %s,
                    description = %s,
                    start_date = %s,
                    end_date = %s,
                    is_active = %s
                WHERE id = %s
                """,
                (name, description, start_date, end_date, is_active, project_id),
            )
        conn.commit()


def toggle_project_active(database_url: str, project_id: int, is_active: bool):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE projects
                SET is_active = %s
                WHERE id = %s
                """,
                (is_active, project_id),
            )
        conn.commit()


def get_project_finance_summary(database_url: str, project_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category_type, COALESCE(SUM(amount), 0) AS total_amount
                FROM finance_records
                WHERE project_id = %s
                GROUP BY category_type
                """,
                (project_id,),
            )
            rows = cur.fetchall()

    total_income = 0
    total_expense = 0

    for row in rows:
        if row["category_type"] == "income":
            total_income = float(row["total_amount"] or 0)
        elif row["category_type"] == "expense":
            total_expense = float(row["total_amount"] or 0)

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_amount": total_income - total_expense,
    }


def get_project_finance_records(database_url: str, project_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id,
                       record_date,
                       category_type,
                       category_name,
                       item_name,
                       amount,
                       payment_method,
                       counterparty,
                       note,
                       created_at
                FROM finance_records
                WHERE project_id = %s
                ORDER BY record_date DESC, id DESC
                """,
                (project_id,),
            )
            return cur.fetchall()


def get_project_ar_ap_records(database_url: str, project_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id,
                       record_type,
                       title,
                       counterparty,
                       amount,
                       due_date,
                       status,
                       note,
                       finance_record_id,
                       paid_received_at,
                       created_at
                FROM receivable_payable_records
                WHERE project_id = %s
                ORDER BY due_date ASC NULLS LAST, id DESC
                """,
                (project_id,),
            )
            return cur.fetchall()


def get_project_profit_report(database_url: str, project_id: int):
    summary = get_project_finance_summary(database_url, project_id)

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category_type,
                       category_name,
                       SUM(amount) AS total_amount
                FROM finance_records
                WHERE project_id = %s
                GROUP BY category_type, category_name
                ORDER BY category_type ASC, total_amount DESC
                """,
                (project_id,),
            )
            category_rows = cur.fetchall()

    income_by_category = [r for r in category_rows if r["category_type"] == "income"]
    expense_by_category = [r for r in category_rows if r["category_type"] == "expense"]

    return {
        **summary,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category,
    }