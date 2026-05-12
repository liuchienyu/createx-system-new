from database import get_db


def calculate_grade(total_score: int) -> str:
    if total_score >= 90:
        return "S"
    if total_score >= 80:
        return "A"
    if total_score >= 70:
        return "B"
    if total_score >= 60:
        return "C"
    return "D"


def calculate_total_score(data: dict) -> tuple[int, str]:
    total = (
        int(data.get("appearance_score") or 0)
        + int(data.get("performance_score") or 0)
        + int(data.get("social_score") or 0)
        + int(data.get("commercial_score") or 0)
        + int(data.get("team_fit_score") or 0)
        + int(data.get("growth_score") or 0)
        - int(data.get("risk_score") or 0)
    )

    if total < 0:
        total = 0

    if total > 100:
        total = 100

    return total, calculate_grade(total)


def list_talents(database_url: str, status: str = ""):
    query = """
        SELECT id, stage_name, real_name, nationality, team_name,
               agency_name, status, created_at
        FROM talents
    """
    params = []

    if status:
        query += " WHERE status = %s"
        params.append(status)

    query += " ORDER BY id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_talent(database_url: str, talent_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM talents WHERE id = %s", (talent_id,))
            return cur.fetchone()


def create_talent(database_url: str, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO talents (
                    stage_name, real_name, gender, nationality, birthday,
                    team_name, agency_name, instagram_url, tiktok_url,
                    youtube_url, contact_info, status, notes, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    data["stage_name"],
                    data["real_name"],
                    data["gender"],
                    data["nationality"],
                    data["birthday"],
                    data["team_name"],
                    data["agency_name"],
                    data["instagram_url"],
                    data["tiktok_url"],
                    data["youtube_url"],
                    data["contact_info"],
                    data["status"],
                    data["notes"],
                    data["created_by"],
                ),
            )
            talent_id = cur.fetchone()["id"]
        conn.commit()

    return talent_id


def update_talent(database_url: str, talent_id: int, data: dict):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE talents
                SET stage_name = %s,
                    real_name = %s,
                    gender = %s,
                    nationality = %s,
                    birthday = %s,
                    team_name = %s,
                    agency_name = %s,
                    instagram_url = %s,
                    tiktok_url = %s,
                    youtube_url = %s,
                    contact_info = %s,
                    status = %s,
                    notes = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    data["stage_name"],
                    data["real_name"],
                    data["gender"],
                    data["nationality"],
                    data["birthday"],
                    data["team_name"],
                    data["agency_name"],
                    data["instagram_url"],
                    data["tiktok_url"],
                    data["youtube_url"],
                    data["contact_info"],
                    data["status"],
                    data["notes"],
                    talent_id,
                ),
            )
        conn.commit()


def delete_talent(database_url: str, talent_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM talents WHERE id = %s", (talent_id,))
        conn.commit()


def list_evaluations(database_url: str, talent_id: int | None = None):
    query = """
        SELECT te.id, te.talent_id, te.report_title, te.evaluation_date,
               te.total_score, te.grade, te.status,
               t.stage_name
        FROM talent_evaluations te
        JOIN talents t ON t.id = te.talent_id
    """
    params = []

    if talent_id:
        query += " WHERE te.talent_id = %s"
        params.append(talent_id)

    query += " ORDER BY te.evaluation_date DESC, te.id DESC"

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_evaluation(database_url: str, evaluation_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT te.*, t.stage_name
                FROM talent_evaluations te
                JOIN talents t ON t.id = te.talent_id
                WHERE te.id = %s
                """,
                (evaluation_id,),
            )
            return cur.fetchone()


def create_evaluation(database_url: str, data: dict):
    total_score, grade = calculate_total_score(data)

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO talent_evaluations (
                    talent_id, report_title, evaluation_date,
                    appearance_score, performance_score, social_score,
                    commercial_score, team_fit_score, growth_score, risk_score,
                    instagram_followers, tiktok_followers, youtube_subscribers,
                    engagement_rate, business_value, social_analysis,
                    team_fit_analysis, signing_review, investment_model,
                    executive_notes, total_score, grade, status, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    data["talent_id"],
                    data["report_title"],
                    data["evaluation_date"],
                    data["appearance_score"],
                    data["performance_score"],
                    data["social_score"],
                    data["commercial_score"],
                    data["team_fit_score"],
                    data["growth_score"],
                    data["risk_score"],
                    data["instagram_followers"],
                    data["tiktok_followers"],
                    data["youtube_subscribers"],
                    data["engagement_rate"],
                    data["business_value"],
                    data["social_analysis"],
                    data["team_fit_analysis"],
                    data["signing_review"],
                    data["investment_model"],
                    data["executive_notes"],
                    total_score,
                    grade,
                    data["status"],
                    data["created_by"],
                ),
            )
            evaluation_id = cur.fetchone()["id"]
        conn.commit()

    return evaluation_id


def delete_evaluation(database_url: str, evaluation_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM talent_evaluations WHERE id = %s", (evaluation_id,))
        conn.commit()