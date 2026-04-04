from datetime import datetime
from database import get_db


def get_leave_types(database_url: str, only_active: bool = True):
    query = """
        SELECT id, code, name, is_paid, sort_order, is_active
        FROM leave_types
    """
    if only_active:
        query += " WHERE is_active = TRUE"
    query += " ORDER BY sort_order ASC, id ASC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def calculate_leave_hours(start_dt: str, end_dt: str) -> float:
    start = datetime.fromisoformat(start_dt)
    end = datetime.fromisoformat(end_dt)
    if end <= start:
        return 0
    return round((end - start).total_seconds() / 3600, 2)


def list_leave_requests(database_url: str, status: str = "", employee_id: str = ""):
    query = """
        SELECT lr.id,
               lr.employee_id,
               lr.start_datetime,
               lr.end_datetime,
               lr.hours,
               lr.reason,
               lr.status,
               lr.approved_at,
               lr.approval_note,
               e.name AS employee_name,
               e.employee_no,
               lt.name AS leave_type_name,
               u.display_name AS approved_by_name
        FROM leave_requests lr
        JOIN employees e ON e.id = lr.employee_id
        JOIN leave_types lt ON lt.id = lr.leave_type_id
        LEFT JOIN users u ON u.id = lr.approved_by
    """
    conditions = []
    params = []

    if status:
        conditions.append("lr.status = %s")
        params.append(status)

    if employee_id:
        conditions.append("lr.employee_id = %s")
        params.append(int(employee_id))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY lr.created_at DESC, lr.id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_leave_request(database_url: str, request_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT lr.*,
                       e.name AS employee_name,
                       e.employee_no,
                       lt.name AS leave_type_name,
                       u.display_name AS approved_by_name
                FROM leave_requests lr
                JOIN employees e ON e.id = lr.employee_id
                JOIN leave_types lt ON lt.id = lr.leave_type_id
                LEFT JOIN users u ON u.id = lr.approved_by
                WHERE lr.id = %s
                """,
                (request_id,),
            )
            return cur.fetchone()


def create_leave_request(database_url: str, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leave_requests (
                    employee_id, leave_type_id, start_datetime, end_datetime,
                    hours, reason, status, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)
                """,
                (
                    data["employee_id"],
                    data["leave_type_id"],
                    data["start_datetime"],
                    data["end_datetime"],
                    data["hours"],
                    data["reason"],
                    data["created_by"],
                ),
            )
        conn.commit()


def approve_leave_request(database_url: str, request_id: int, action: str, approval_note: str, approved_by: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leave_requests
                SET status = %s,
                    approved_by = %s,
                    approved_at = NOW(),
                    approval_note = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (action, approved_by, approval_note, request_id),
            )
        conn.commit()


def delete_leave_request(database_url: str, request_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM leave_requests WHERE id = %s", (request_id,))
        conn.commit()


def disable_leave_type(database_url: str, type_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leave_types
                SET is_active = FALSE
                WHERE id = %s
                """,
                (type_id,),
            )
        conn.commit()