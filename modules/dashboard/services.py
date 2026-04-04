from datetime import datetime
from zoneinfo import ZoneInfo

from database import get_db

TW = ZoneInfo("Asia/Taipei")


def get_dashboard_base_context(database_url: str, user_id: int):
    now = datetime.now(TW)
    today = now.date()
    current_month = f"{now.year:04d}-{now.month:02d}"
    return {
        "current_time": now,
        "today": today,
        "current_month": current_month,
        "user_id": user_id,
    }


def get_finance_dashboard_summary(database_url: str, month: str):
    start_date = f"{month}-01"

    year, month_no = month.split("-")
    year = int(year)
    month_no = int(month_no)

    if month_no == 12:
        end_date = f"{year + 1:04d}-01-01"
    else:
        end_date = f"{year:04d}-{month_no + 1:02d}-01"

    total_income = 0
    total_expense = 0
    recent_finance_records = []

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category_type, COALESCE(SUM(amount), 0) AS total_amount
                FROM finance_records
                WHERE record_date >= %s
                  AND record_date < %s
                GROUP BY category_type
                """,
                (start_date, end_date),
            )
            rows = cur.fetchall()

            for row in rows:
                if row["category_type"] == "income":
                    total_income = float(row["total_amount"] or 0)
                elif row["category_type"] == "expense":
                    total_expense = float(row["total_amount"] or 0)

            cur.execute(
                """
                SELECT id, record_date, category_type, category_name, item_name, amount
                FROM finance_records
                ORDER BY record_date DESC, id DESC
                LIMIT 5
                """
            )
            recent_finance_records = cur.fetchall()

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_amount": total_income - total_expense,
        "recent_finance_records": recent_finance_records,
    }


def get_project_dashboard_summary(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM projects
                WHERE is_active = TRUE
                """
            )
            active_project_count = cur.fetchone()["cnt"]

            cur.execute(
                """
                SELECT p.id, p.name,
                       COALESCE(SUM(CASE WHEN fr.category_type = 'income' THEN fr.amount ELSE 0 END), 0) AS total_income,
                       COALESCE(SUM(CASE WHEN fr.category_type = 'expense' THEN fr.amount ELSE 0 END), 0) AS total_expense
                FROM projects p
                LEFT JOIN finance_records fr ON fr.project_id = p.id
                GROUP BY p.id
                ORDER BY p.id DESC
                LIMIT 5
                """
            )
            rows = cur.fetchall()

    top_projects = []
    for row in rows:
        income = float(row["total_income"] or 0)
        expense = float(row["total_expense"] or 0)
        top_projects.append({
            "id": row["id"],
            "name": row["name"],
            "total_income": income,
            "total_expense": expense,
            "net_amount": income - expense,
        })

    return {
        "active_project_count": active_project_count,
        "top_projects": top_projects,
    }


def get_hr_dashboard_summary(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status, COUNT(*) AS cnt
                FROM employees
                GROUP BY status
                """
            )
            rows = cur.fetchall()

            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM departments
                WHERE is_active = TRUE
                """
            )
            active_department_count = cur.fetchone()["cnt"]

            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM job_titles
                WHERE is_active = TRUE
                """
            )
            active_job_title_count = cur.fetchone()["cnt"]

    stats = {
        "employee_active_count": 0,
        "employee_probation_count": 0,
        "employee_leave_count": 0,
        "employee_terminated_count": 0,
        "employee_archived_count": 0,
        "active_department_count": active_department_count,
        "active_job_title_count": active_job_title_count,
    }

    for row in rows:
        status = row["status"]
        cnt = row["cnt"]
        if status == "active":
            stats["employee_active_count"] = cnt
        elif status == "probation":
            stats["employee_probation_count"] = cnt
        elif status == "leave":
            stats["employee_leave_count"] = cnt
        elif status == "terminated":
            stats["employee_terminated_count"] = cnt
        elif status == "archived":
            stats["employee_archived_count"] = cnt

    return stats


def get_leave_pending_summary(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT lr.id,
                       e.employee_no,
                       e.name AS employee_name,
                       lt.name AS leave_type_name,
                       lr.start_datetime,
                       lr.end_datetime,
                       lr.hours
                FROM leave_requests lr
                JOIN employees e ON e.id = lr.employee_id
                JOIN leave_types lt ON lt.id = lr.leave_type_id
                WHERE lr.status = 'pending'
                ORDER BY lr.created_at ASC, lr.id ASC
                LIMIT 10
                """
            )
            pending_leave_requests = cur.fetchall()

    return {
        "pending_leave_count": len(pending_leave_requests),
        "pending_leave_requests": pending_leave_requests,
    }


def get_my_attendance_summary(database_url: str, user_id: int, today):
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
            employee = cur.fetchone()

            if not employee:
                return {
                    "my_employee": None,
                    "today_attendance": None,
                }

            cur.execute(
                """
                SELECT id, attendance_date, check_in_time, check_out_time, status, note
                FROM attendance_records
                WHERE employee_id = %s
                  AND attendance_date = %s
                """,
                (employee["id"], today),
            )
            today_attendance = cur.fetchone()

    return {
        "my_employee": employee,
        "today_attendance": today_attendance,
    }


def get_ar_ap_summary(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT record_type, COALESCE(SUM(amount), 0) AS total_amount
                FROM receivable_payable_records
                WHERE status = 'pending'
                GROUP BY record_type
                """
            )
            rows = cur.fetchall()

    total_receivable = 0
    total_payable = 0

    for row in rows:
        if row["record_type"] == "receivable":
            total_receivable = float(row["total_amount"] or 0)
        elif row["record_type"] == "payable":
            total_payable = float(row["total_amount"] or 0)

    return {
        "total_receivable": total_receivable,
        "total_payable": total_payable,
    }


def build_dashboard_context(database_url: str, user_id: int):
    base = get_dashboard_base_context(database_url, user_id)
    month = base["current_month"]
    today = base["today"]

    context = {
        **base,
        **get_finance_dashboard_summary(database_url, month),
        **get_project_dashboard_summary(database_url),
        **get_hr_dashboard_summary(database_url),
        **get_leave_pending_summary(database_url),
        **get_my_attendance_summary(database_url, user_id, today),
        **get_ar_ap_summary(database_url),
    }
    return context