from database import get_db


def generate_employee_no(database_url: str) -> str:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM employees")
            cnt = cur.fetchone()["cnt"] + 1
    return f"E{cnt:04d}"


def list_employees(database_url: str, status: str = ""):
    query = """
        SELECT e.id,
               e.employee_no,
               e.name,
               e.phone,
               e.email,
               e.status,
               e.hire_date,
               e.department_id,
               e.job_title_id,
               d.name AS department_name,
               jt.name AS job_title_name,
               u.username
        FROM employees e
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN departments d ON d.id = e.department_id
        LEFT JOIN job_titles jt ON jt.id = e.job_title_id
    """
    params = []

    if status:
        query += " WHERE e.status = %s"
        params.append(status)

    query += " ORDER BY e.id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_employee(database_url: str, employee_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.*,
                       u.username,
                       u.display_name AS user_display_name,
                       d.name AS department_name,
                       jt.name AS job_title_name,
                       m.name AS manager_name
                FROM employees e
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN departments d ON d.id = e.department_id
                LEFT JOIN job_titles jt ON jt.id = e.job_title_id
                LEFT JOIN employees m ON m.id = e.manager_employee_id
                WHERE e.id = %s
                """,
                (employee_id,),
            )
            return cur.fetchone()


def list_active_employees_basic(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, employee_no, name
                FROM employees
                WHERE status IN ('active', 'probation', 'leave')
                ORDER BY id DESC
                """
            )
            return cur.fetchall()


def list_available_users(database_url: str, include_user_id: int | None = None):
    query = """
        SELECT id, username, display_name
        FROM users
        WHERE is_active = TRUE
          AND (
                id NOT IN (
                    SELECT user_id
                    FROM employees
                    WHERE user_id IS NOT NULL
                )
    """
    params = []

    if include_user_id is not None:
        query += " OR id = %s"
        params.append(include_user_id)

    query += ") ORDER BY id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def create_employee(database_url: str, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO employees (
                    user_id, employee_no, name, english_name, nickname, gender, birthday,
                    phone, email, address, emergency_contact_name, emergency_contact_phone,
                    status, hire_date, leave_date, department_id, job_title_id,
                    manager_employee_id, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    data["user_id"],
                    data["employee_no"],
                    data["name"],
                    data["english_name"],
                    data["nickname"],
                    data["gender"],
                    data["birthday"],
                    data["phone"],
                    data["email"],
                    data["address"],
                    data["emergency_contact_name"],
                    data["emergency_contact_phone"],
                    data["status"],
                    data["hire_date"],
                    data["leave_date"],
                    data["department_id"],
                    data["job_title_id"],
                    data["manager_employee_id"],
                    data["notes"],
                ),
            )
            employee_id = cur.fetchone()["id"]
        conn.commit()
    return employee_id


def update_employee(database_url: str, employee_id: int, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE employees
                SET user_id = %s,
                    employee_no = %s,
                    name = %s,
                    english_name = %s,
                    nickname = %s,
                    gender = %s,
                    birthday = %s,
                    phone = %s,
                    email = %s,
                    address = %s,
                    emergency_contact_name = %s,
                    emergency_contact_phone = %s,
                    status = %s,
                    hire_date = %s,
                    leave_date = %s,
                    department_id = %s,
                    job_title_id = %s,
                    manager_employee_id = %s,
                    notes = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    data["user_id"],
                    data["employee_no"],
                    data["name"],
                    data["english_name"],
                    data["nickname"],
                    data["gender"],
                    data["birthday"],
                    data["phone"],
                    data["email"],
                    data["address"],
                    data["emergency_contact_name"],
                    data["emergency_contact_phone"],
                    data["status"],
                    data["hire_date"],
                    data["leave_date"],
                    data["department_id"],
                    data["job_title_id"],
                    data["manager_employee_id"],
                    data["notes"],
                    employee_id,
                ),
            )
        conn.commit()


def archive_employee(database_url: str, employee_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE employees
                SET status = 'archived',
                    updated_at = NOW()
                WHERE id = %s
                """,
                (employee_id,),
            )
        conn.commit()


def get_employee_movements(database_url: str, employee_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT em.id,
                       em.movement_type,
                       em.effective_date,
                       em.from_status,
                       em.to_status,
                       em.remark,
                       fd.name AS from_department_name,
                       td.name AS to_department_name,
                       fjt.name AS from_job_title_name,
                       tjt.name AS to_job_title_name,
                       u.display_name AS created_by_name
                FROM employee_movements em
                LEFT JOIN departments fd ON fd.id = em.from_department_id
                LEFT JOIN departments td ON td.id = em.to_department_id
                LEFT JOIN job_titles fjt ON fjt.id = em.from_job_title_id
                LEFT JOIN job_titles tjt ON tjt.id = em.to_job_title_id
                LEFT JOIN users u ON u.id = em.created_by
                WHERE em.employee_id = %s
                ORDER BY em.effective_date DESC, em.id DESC
                """,
                (employee_id,),
            )
            return cur.fetchall()


def get_employee_leave_requests(database_url: str, employee_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT lr.id,
                       lr.start_datetime,
                       lr.end_datetime,
                       lr.hours,
                       lr.reason,
                       lr.status,
                       lt.name AS leave_type_name
                FROM leave_requests lr
                JOIN leave_types lt ON lt.id = lr.leave_type_id
                WHERE lr.employee_id = %s
                ORDER BY lr.start_datetime DESC, lr.id DESC
                LIMIT 10
                """,
                (employee_id,),
            )
            return cur.fetchall()


def get_employee_attendance_records(database_url: str, employee_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, attendance_date, check_in_time, check_out_time, status, note
                FROM attendance_records
                WHERE employee_id = %s
                ORDER BY attendance_date DESC, id DESC
                LIMIT 10
                """,
                (employee_id,),
            )
            return cur.fetchall()