from datetime import date
from database import get_db


def list_attendance_records(database_url: str, employee_id: str = "", attendance_date: str = ""):
    query = """
        SELECT ar.id,
               ar.employee_id,
               ar.attendance_date,
               ar.check_in_time,
               ar.check_out_time,
               ar.status,
               ar.note,
               e.employee_no,
               e.name AS employee_name
        FROM attendance_records ar
        JOIN employees e ON e.id = ar.employee_id
    """
    conditions = []
    params = []

    if employee_id:
        conditions.append("ar.employee_id = %s")
        params.append(int(employee_id))

    if attendance_date:
        conditions.append("ar.attendance_date = %s")
        params.append(attendance_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY ar.attendance_date DESC, ar.id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def create_manual_attendance(database_url: str, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO attendance_records (
                    employee_id, attendance_date, check_in_time, check_out_time,
                    status, note, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (employee_id, attendance_date)
                DO UPDATE SET
                    check_in_time = EXCLUDED.check_in_time,
                    check_out_time = EXCLUDED.check_out_time,
                    status = EXCLUDED.status,
                    note = EXCLUDED.note,
                    updated_at = NOW()
                """,
                (
                    data["employee_id"],
                    data["attendance_date"],
                    data["check_in_time"],
                    data["check_out_time"],
                    data["status"],
                    data["note"],
                    data["created_by"],
                ),
            )
        conn.commit()


def delete_attendance_record(database_url: str, record_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM attendance_records WHERE id = %s", (record_id,))
        conn.commit()


def get_employee_by_user_id(database_url: str, user_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, employee_no, name, status
                FROM employees
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return cur.fetchone()


def get_today_attendance(database_url: str, employee_id: int, attendance_date: date):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM attendance_records
                WHERE employee_id = %s AND attendance_date = %s
                """,
                (employee_id, attendance_date),
            )
            return cur.fetchone()


def clock_in(database_url: str, employee_id: int, attendance_date, now_dt, created_by: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO attendance_records (
                    employee_id, attendance_date, check_in_time, status, created_by
                )
                VALUES (%s, %s, %s, 'present', %s)
                ON CONFLICT (employee_id, attendance_date)
                DO UPDATE SET
                    check_in_time = COALESCE(attendance_records.check_in_time, EXCLUDED.check_in_time),
                    updated_at = NOW()
                """,
                (employee_id, attendance_date, now_dt, created_by),
            )
        conn.commit()


def clock_out(database_url: str, employee_id: int, attendance_date, now_dt):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE attendance_records
                SET check_out_time = %s,
                    updated_at = NOW()
                WHERE employee_id = %s
                  AND attendance_date = %s
                """,
                (now_dt, employee_id, attendance_date),
            )
        conn.commit()