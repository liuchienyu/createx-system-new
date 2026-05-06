from database import get_db


def list_approval_templates(database_url: str, active_filter: str = ""):
    query = """
        SELECT id, template_name, doc_type, title_template, content_template,
               is_active, allow_pdf_export, is_fixed_flow
        FROM approval_templates
    """
    params = []

    if active_filter == "true":
        query += " WHERE is_active = TRUE"
    elif active_filter == "false":
        query += " WHERE is_active = FALSE"

    query += " ORDER BY id ASC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_approval_template(database_url: str, template_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, template_name, doc_type, title_template, content_template,
                       is_active, allow_pdf_export, is_fixed_flow
                FROM approval_templates
                WHERE id = %s
                """,
                (template_id,),
            )
            return cur.fetchone()


def get_template_steps(database_url: str, template_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, step_no, approver_user_id, approver_name
                FROM approval_template_steps
                WHERE template_id = %s
                ORDER BY step_no ASC
                """,
                (template_id,),
            )
            return cur.fetchall()


def create_approval_template(database_url: str, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                                INSERT INTO approval_templates (
                    template_name, doc_type, title_template, content_template,
                    is_active, allow_pdf_export, is_fixed_flow
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    data["template_name"],
                    data["doc_type"],
                    data["title_template"],
                    data["content_template"],
                    data["is_active"],
                    data["allow_pdf_export"],
                    data["is_fixed_flow"],
                ),
            )
            template_id = cur.fetchone()["id"]

            for idx, step in enumerate(data["steps"], start=1):
                cur.execute(
                    """
                    INSERT INTO approval_template_steps (
                        template_id, step_no, approver_user_id, approver_name
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        template_id,
                        idx,
                        step["approver_user_id"],
                        step["approver_name"],
                    ),
                )
        conn.commit()

    return template_id

def update_approval_template(database_url: str, template_id: int, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE approval_templates
                SET template_name = %s,
                    doc_type = %s,
                    title_template = %s,
                    content_template = %s,
                    is_active = %s,
                    allow_pdf_export = %s,
                    is_fixed_flow = %s
                WHERE id = %s
                """,
                (
                    data["template_name"],
                    data["doc_type"],
                    data["title_template"],
                    data["content_template"],
                    data["is_active"],
                    data["allow_pdf_export"],
                    data["is_fixed_flow"],
                    template_id,
                ),
            )

            cur.execute(
                """
                DELETE FROM approval_template_steps
                WHERE template_id = %s
                """,
                (template_id,),
            )

            for idx, step in enumerate(data["steps"], start=1):
                cur.execute(
                    """
                    INSERT INTO approval_template_steps (
                        template_id, step_no, approver_user_id, approver_name
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        template_id,
                        idx,
                        step["approver_user_id"],
                        step["approver_name"],
                    ),
                )

        conn.commit()

def disable_approval_template(database_url: str, template_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE approval_templates
                SET is_active = FALSE
                WHERE id = %s
                """,
                (template_id,),
            )
        conn.commit()