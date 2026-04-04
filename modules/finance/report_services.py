from database import get_db
from modules.finance.services import parse_month_filter


def get_finance_dashboard_data(database_url: str, month: str):
    start_date, end_date = parse_month_filter(month)

    total_income = 0
    total_expense = 0
    recent_records = []
    top_expense_categories = []

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category_type, COALESCE(SUM(amount), 0) AS total_amount
                FROM finance_records
                WHERE record_date >= %s AND record_date < %s
                GROUP BY category_type
                """,
                (start_date, end_date),
            )
            summary_rows = cur.fetchall()

            for row in summary_rows:
                if row["category_type"] == "income":
                    total_income = float(row["total_amount"] or 0)
                elif row["category_type"] == "expense":
                    total_expense = float(row["total_amount"] or 0)

            cur.execute(
                """
                SELECT fr.id,
                       fr.record_date,
                       fr.category_type,
                       fr.category_name,
                       fr.item_name,
                       fr.amount,
                       fr.payment_method,
                       fr.counterparty,
                       u.display_name AS created_by_name
                FROM finance_records fr
                LEFT JOIN users u ON u.id = fr.created_by
                ORDER BY fr.record_date DESC, fr.id DESC
                LIMIT 10
                """
            )
            recent_records = cur.fetchall()

            cur.execute(
                """
                SELECT category_name,
                       SUM(amount) AS total_amount
                FROM finance_records
                WHERE record_date >= %s
                  AND record_date < %s
                  AND category_type = 'expense'
                GROUP BY category_name
                ORDER BY total_amount DESC
                LIMIT 5
                """,
                (start_date, end_date),
            )
            top_expense_categories = cur.fetchall()

    return {
        "month": month,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_amount": total_income - total_expense,
        "recent_records": recent_records,
        "top_expense_categories": top_expense_categories,
    }


def get_monthly_report_data(database_url: str, month: str):
    start_date, end_date = parse_month_filter(month)

    if not start_date or not end_date:
        return {
            "summary": [],
            "total_income": 0,
            "total_expense": 0,
            "net_amount": 0,
            "income_by_category": [],
            "expense_by_category": [],
        }

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category_type,
                       category_name,
                       SUM(amount) AS total_amount
                FROM finance_records
                WHERE record_date >= %s AND record_date < %s
                GROUP BY category_type, category_name
                ORDER BY category_type ASC, total_amount DESC
                """,
                (start_date, end_date),
            )
            summary = cur.fetchall()

    income_by_category = [r for r in summary if r["category_type"] == "income"]
    expense_by_category = [r for r in summary if r["category_type"] == "expense"]

    total_income = sum(float(r["total_amount"]) for r in income_by_category)
    total_expense = sum(float(r["total_amount"]) for r in expense_by_category)

    return {
        "summary": summary,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_amount": total_income - total_expense,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category,
    }