from database import get_db


def list_ar_ap_records(database_url: str, record_type: str = "", status: str = ""):
    query = """
        SELECT rp.id,
               rp.record_type,
               rp.title,
               rp.counterparty,
               rp.amount,
               rp.due_date,
               rp.status,
               rp.note,
               rp.project_id,
               rp.finance_record_id,
               rp.paid_received_at,
               p.name AS project_name
        FROM receivable_payable_records rp
        LEFT JOIN projects p ON p.id = rp.project_id
    """
    conditions = []
    params = []

    if record_type in ["receivable", "payable"]:
        conditions.append("rp.record_type = %s")
        params.append(record_type)

    if status in ["pending", "completed", "cancelled"]:
        conditions.append("rp.status = %s")
        params.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY rp.due_date ASC NULLS LAST, rp.id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_ar_ap_record(database_url: str, record_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM receivable_payable_records
                WHERE id = %s
                """,
                (record_id,),
            )
            return cur.fetchone()


def create_ar_ap_record(
    database_url: str,
    record_type: str,
    title: str,
    counterparty: str,
    amount: float,
    due_date: str | None,
    status: str,
    note: str,
    project_id: int | None,
    created_by: int,
):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO receivable_payable_records (
                    record_type, title, counterparty, amount, due_date,
                    status, note, project_id, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record_type,
                    title,
                    counterparty,
                    amount,
                    due_date,
                    status,
                    note,
                    project_id,
                    created_by,
                ),
            )
        conn.commit()


def update_ar_ap_record(
    database_url: str,
    record_id: int,
    record_type: str,
    title: str,
    counterparty: str,
    amount: float,
    due_date: str | None,
    status: str,
    note: str,
    project_id: int | None,
):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE receivable_payable_records
                SET record_type = %s,
                    title = %s,
                    counterparty = %s,
                    amount = %s,
                    due_date = %s,
                    status = %s,
                    note = %s,
                    project_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    record_type,
                    title,
                    counterparty,
                    amount,
                    due_date,
                    status,
                    note,
                    project_id,
                    record_id,
                ),
            )
        conn.commit()


def mark_ar_ap_completed(database_url: str, record_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, finance_record_id
                FROM receivable_payable_records
                WHERE id = %s
                """,
                (record_id,),
            )
            record = cur.fetchone()

            if not record:
                return None

            if record["status"] != "completed":
                cur.execute(
                    """
                    UPDATE receivable_payable_records
                    SET status = 'completed',
                        paid_received_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (record_id,),
                )
                conn.commit()

    return True


def create_finance_record_from_ar_ap(database_url: str, record_id: int, created_by: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rp.id,
                       rp.record_type,
                       rp.title,
                       rp.counterparty,
                       rp.amount,
                       rp.due_date,
                       rp.status,
                       rp.note,
                       rp.project_id,
                       rp.finance_record_id
                FROM receivable_payable_records rp
                WHERE rp.id = %s
                """,
                (record_id,),
            )
            rp_record = cur.fetchone()

            if not rp_record:
                return None

            if rp_record["finance_record_id"]:
                return rp_record["finance_record_id"]

            if rp_record["status"] != "completed":
                return None

            category_type = "income" if rp_record["record_type"] == "receivable" else "expense"
            fallback_category_name = "其他收入" if category_type == "income" else "其他支出"

            cur.execute(
                """
                SELECT id, name
                FROM finance_categories
                WHERE category_type = %s
                  AND name = %s
                  AND is_active = TRUE
                LIMIT 1
                """,
                (category_type, fallback_category_name),
            )
            category = cur.fetchone()

            if not category:
                cur.execute(
                    """
                    SELECT id, name
                    FROM finance_categories
                    WHERE category_type = %s
                      AND is_active = TRUE
                    ORDER BY sort_order ASC, id ASC
                    LIMIT 1
                    """,
                    (category_type,),
                )
                category = cur.fetchone()

            if not category:
                raise RuntimeError(f"找不到可用的財務分類：{category_type}")

            record_date = rp_record["due_date"]
            if not record_date:
                cur.execute("SELECT CURRENT_DATE AS today")
                record_date = cur.fetchone()["today"]

            finance_note = rp_record["note"] or ""
            finance_note = f"[由應收應付自動轉入] {finance_note}".strip()

            cur.execute(
                """
                INSERT INTO finance_records (
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
                    project_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    record_date,
                    category_type,
                    category["id"],
                    category["name"],
                    rp_record["title"],
                    rp_record["amount"],
                    "應收應付轉入",
                    rp_record["counterparty"],
                    finance_note,
                    created_by,
                    rp_record["project_id"],
                ),
            )
            finance_record_id = cur.fetchone()["id"]

            cur.execute(
                """
                UPDATE receivable_payable_records
                SET finance_record_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (finance_record_id, record_id),
            )
            conn.commit()

            return finance_record_id