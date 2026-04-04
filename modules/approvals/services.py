from database import get_db


def generate_doc_no(database_url: str) -> str:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM approval_documents")
            cnt = cur.fetchone()["cnt"] + 1
    return f"APP-{cnt:05d}"


def list_documents(database_url: str, status: str = "", applicant_user_id: str = ""):
    query = """
        SELECT d.id,
               d.doc_no,
               d.title,
               d.doc_type,
               d.applicant_user_id,
               d.applicant_name,
               d.status,
               d.current_step,
               d.current_approver_user_id,
               d.submitted_at,
               d.completed_at,
               d.rejected_at,
               d.created_at,
               u.display_name AS current_approver_name
        FROM approval_documents d
        LEFT JOIN users u ON u.id = d.current_approver_user_id
    """
    conditions = []
    params = []

    if status:
        conditions.append("d.status = %s")
        params.append(status)

    if applicant_user_id:
        conditions.append("d.applicant_user_id = %s")
        params.append(int(applicant_user_id))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY d.created_at DESC, d.id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_document(database_url: str, document_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.*
                FROM approval_documents d
                WHERE d.id = %s
                """,
                (document_id,),
            )
            return cur.fetchone()


def get_document_steps(database_url: str, document_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id,
                       s.step_no,
                       s.approver_user_id,
                       s.approver_name,
                       s.action_status,
                       s.action_note,
                       s.acted_at
                FROM approval_steps s
                WHERE s.document_id = %s
                ORDER BY s.step_no ASC
                """,
                (document_id,),
            )
            return cur.fetchall()


def list_approver_users(database_url: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, display_name
                FROM users
                WHERE is_active = TRUE
                ORDER BY id ASC
                """
            )
            return cur.fetchall()


def create_document(database_url: str, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO approval_documents (
                    doc_no, title, doc_type, applicant_user_id, applicant_name,
                    content, status, current_step, current_approver_user_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'draft', 0, NULL)
                RETURNING id
                """,
                (
                    data["doc_no"],
                    data["title"],
                    data["doc_type"],
                    data["applicant_user_id"],
                    data["applicant_name"],
                    data["content"],
                ),
            )
            document_id = cur.fetchone()["id"]

            for idx, step in enumerate(data["steps"], start=1):
                cur.execute(
                    """
                    INSERT INTO approval_steps (
                        document_id, step_no, approver_user_id, approver_name, action_status
                    )
                    VALUES (%s, %s, %s, %s, 'pending')
                    """,
                    (
                        document_id,
                        idx,
                        step["approver_user_id"],
                        step["approver_name"],
                    ),
                )

        conn.commit()

    return document_id


def submit_document(database_url: str, document_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status
                FROM approval_documents
                WHERE id = %s
                """,
                (document_id,),
            )
            doc = cur.fetchone()

            if not doc:
                return False, "公文不存在"

            if doc["status"] != "draft":
                return False, "只有草稿狀態可送出"

            cur.execute(
                """
                SELECT step_no, approver_user_id
                FROM approval_steps
                WHERE document_id = %s
                ORDER BY step_no ASC
                LIMIT 1
                """,
                (document_id,),
            )
            first_step = cur.fetchone()

            if not first_step:
                return False, "此公文未設定簽核人"

            cur.execute(
                """
                UPDATE approval_documents
                SET status = 'pending',
                    current_step = %s,
                    current_approver_user_id = %s,
                    submitted_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (first_step["step_no"], first_step["approver_user_id"], document_id),
            )

        conn.commit()

    return True, "公文已送出簽核"


def list_my_pending_documents(database_url: str, approver_user_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.id,
                       d.doc_no,
                       d.title,
                       d.doc_type,
                       d.applicant_name,
                       d.status,
                       d.current_step,
                       d.submitted_at
                FROM approval_documents d
                WHERE d.status = 'pending'
                  AND d.current_approver_user_id = %s
                ORDER BY d.submitted_at ASC, d.id ASC
                """,
                (approver_user_id,),
            )
            return cur.fetchall()


def approve_document(database_url: str, document_id: int, approver_user_id: int, action: str, note: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, current_step, current_approver_user_id
                FROM approval_documents
                WHERE id = %s
                """,
                (document_id,),
            )
            doc = cur.fetchone()

            if not doc:
                return False, "公文不存在"

            if doc["status"] != "pending":
                return False, "此公文目前不可簽核"

            if doc["current_approver_user_id"] != approver_user_id:
                return False, "目前不是你的簽核節點"

            cur.execute(
                """
                UPDATE approval_steps
                SET action_status = %s,
                    action_note = %s,
                    acted_at = NOW()
                WHERE document_id = %s
                  AND step_no = %s
                """,
                (action, note, document_id, doc["current_step"]),
            )

            if action == "rejected":
                cur.execute(
                    """
                    UPDATE approval_documents
                    SET status = 'rejected',
                        rejected_at = NOW(),
                        current_approver_user_id = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (document_id,),
                )
                conn.commit()
                return True, "公文已退回"

            cur.execute(
                """
                SELECT step_no, approver_user_id
                FROM approval_steps
                WHERE document_id = %s
                  AND step_no > %s
                ORDER BY step_no ASC
                LIMIT 1
                """,
                (document_id, doc["current_step"]),
            )
            next_step = cur.fetchone()

            if next_step:
                cur.execute(
                    """
                    UPDATE approval_documents
                    SET current_step = %s,
                        current_approver_user_id = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (next_step["step_no"], next_step["approver_user_id"], document_id),
                )
                conn.commit()
                return True, "已核准，並送往下一關"

            cur.execute(
                """
                UPDATE approval_documents
                SET status = 'approved',
                    completed_at = NOW(),
                    current_approver_user_id = NULL,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (document_id,),
            )

        conn.commit()

    return True, "公文已完成核准"

def create_document_from_template(database_url: str, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, template_name, doc_type, title_template, content_template, is_active
                FROM approval_templates
                WHERE id = %s
                """,
                (data["template_id"],),
            )
            template = cur.fetchone()

            if not template:
                return None, "模板不存在"

            if not template["is_active"]:
                return None, "模板已停用"

            cur.execute(
                """
                SELECT step_no, approver_user_id, approver_name
                FROM approval_template_steps
                WHERE template_id = %s
                ORDER BY step_no ASC
                """,
                (data["template_id"],),
            )
            template_steps = cur.fetchall()

            if not template_steps:
                return None, "模板尚未設定簽核流程"

            title = data["title"] or template["title_template"]
            content = data["content"] or template["content_template"]

            cur.execute(
                """
                INSERT INTO approval_documents (
                    doc_no, title, doc_type, applicant_user_id, applicant_name,
                    content, status, current_step, current_approver_user_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'draft', 0, NULL)
                RETURNING id
                """,
                (
                    data["doc_no"],
                    title,
                    template["doc_type"],
                    data["applicant_user_id"],
                    data["applicant_name"],
                    content,
                ),
            )
            document_id = cur.fetchone()["id"]

            for step in template_steps:
                cur.execute(
                    """
                    INSERT INTO approval_steps (
                        document_id, step_no, approver_user_id, approver_name, action_status
                    )
                    VALUES (%s, %s, %s, %s, 'pending')
                    """,
                    (
                        document_id,
                        step["step_no"],
                        step["approver_user_id"],
                        step["approver_name"],
                    ),
                )

        conn.commit()

    return document_id, "已依模板建立公文草稿"