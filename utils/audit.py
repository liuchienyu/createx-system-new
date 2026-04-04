import json
from database import get_db


def write_audit_log(
    database_url: str,
    module_name: str,
    action_type: str,
    target_type: str,
    target_id: int | None,
    actor_user_id: int | None,
    actor_name: str | None,
    summary: str,
    detail_json: dict | None = None,
):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_logs (
                    module_name, action_type, target_type, target_id,
                    actor_user_id, actor_name, summary, detail_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    module_name,
                    action_type,
                    target_type,
                    target_id,
                    actor_user_id,
                    actor_name,
                    summary,
                    json.dumps(detail_json or {}, ensure_ascii=False),
                ),
            )
        conn.commit()