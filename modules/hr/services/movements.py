from database import get_db


def movement_type_options():
    return [
        ("hire", "到職"),
        ("probation_pass", "轉正"),
        ("department_transfer", "調部門"),
        ("promotion", "升遷"),
        ("demotion", "降職"),
        ("leave", "留停"),
        ("reinstate", "復職"),
        ("termination", "離職"),
        ("other", "其他"),
    ]


def list_movements(database_url: str, movement_type: str = ""):
    query = """
        SELECT em.id,
               em.employee_id,
               em.movement_type,
               em.effective_date,
               em.from_status,
               em.to_status,
               em.remark,
               e.name AS employee_name,
               e.employee_no,
               fd.name AS from_department_name,
               td.name AS to_department_name,
               fjt.name AS from_job_title_name,
               tjt.name AS to_job_title_name,
               u.display_name AS created_by_name
        FROM employee_movements em
        JOIN employees e ON e.id = em.employee_id
        LEFT JOIN departments fd ON fd.id = em.from_department_id
        LEFT JOIN departments td ON td.id = em.to_department_id
        LEFT JOIN job_titles fjt ON fjt.id = em.from_job_title_id
        LEFT JOIN job_titles tjt ON tjt.id = em.to_job_title_id
        LEFT JOIN users u ON u.id = em.created_by
    """
    params = []
    if movement_type:
        query += " WHERE em.movement_type = %s"
        params.append(movement_type)
    query += " ORDER BY em.effective_date DESC, em.id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def create_movement(database_url: str, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM employees WHERE id = %s", (data["employee_id"],))
            employee = cur.fetchone()

            cur.execute(
                """
                INSERT INTO employee_movements (
                    employee_id, movement_type, effective_date,
                    from_department_id, to_department_id,
                    from_job_title_id, to_job_title_id,
                    from_status, to_status, remark, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data["employee_id"],
                    data["movement_type"],
                    data["effective_date"],
                    employee["department_id"],
                    data["to_department_id"] if data["to_department_id"] is not None else employee["department_id"],
                    employee["job_title_id"],
                    data["to_job_title_id"] if data["to_job_title_id"] is not None else employee["job_title_id"],
                    employee["status"],
                    data["to_status"] if data["to_status"] else employee["status"],
                    data["remark"],
                    data["created_by"],
                ),
            )

            final_department_id = data["to_department_id"] if data["to_department_id"] is not None else employee["department_id"]
            final_job_title_id = data["to_job_title_id"] if data["to_job_title_id"] is not None else employee["job_title_id"]
            final_status = data["to_status"] if data["to_status"] else employee["status"]

            cur.execute(
                """
                UPDATE employees
                SET department_id = %s,
                    job_title_id = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (final_department_id, final_job_title_id, final_status, data["employee_id"]),
            )

            if data["movement_type"] == "termination":
                cur.execute(
                    "UPDATE employees SET leave_date = %s WHERE id = %s",
                    (data["effective_date"], data["employee_id"]),
                )

            if data["movement_type"] == "hire" and not employee["hire_date"]:
                cur.execute(
                    "UPDATE employees SET hire_date = %s WHERE id = %s",
                    (data["effective_date"], data["employee_id"]),
                )

        conn.commit()


def delete_movement(database_url: str, movement_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM employee_movements WHERE id = %s", (movement_id,))
        conn.commit()