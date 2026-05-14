from __future__ import annotations

from typing import Optional, Set

import psycopg
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash

from permissions import PERMS, DEFAULT_ROLES


def get_db(database_url: str):
    return psycopg.connect(database_url, row_factory=dict_row)


def init_db(database_url: str) -> None:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name VARCHAR(100),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS permissions (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_roles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, role_id)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id SERIAL PRIMARY KEY,
                    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(role_id, permission_id)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    start_date DATE,
                    end_date DATE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS finance_categories (
                    id SERIAL PRIMARY KEY,
                    category_type VARCHAR(20) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(category_type, name)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS finance_records (
                    id SERIAL PRIMARY KEY,
                    record_date DATE NOT NULL,
                    category_type VARCHAR(20) NOT NULL,
                    category_name VARCHAR(100) NOT NULL,
                    item_name VARCHAR(200) NOT NULL,
                    amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
                    payment_method VARCHAR(50),
                    counterparty VARCHAR(100),
                    note TEXT,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                ALTER TABLE finance_records
                ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES finance_categories(id) ON DELETE SET NULL;
                """
            )

            cur.execute(
                """
                ALTER TABLE finance_records
                ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS receivable_payable_records (
                    id SERIAL PRIMARY KEY,
                    record_type VARCHAR(20) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    counterparty VARCHAR(100),
                    amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
                    due_date DATE,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    note TEXT,
                    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                    finance_record_id INTEGER REFERENCES finance_records(id) ON DELETE SET NULL,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    paid_received_at TIMESTAMP NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS departments (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    parent_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS job_titles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    level INTEGER NOT NULL DEFAULT 1,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
                    employee_no VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    english_name VARCHAR(100),
                    nickname VARCHAR(100),
                    gender VARCHAR(20),
                    birthday DATE,
                    phone VARCHAR(50),
                    email VARCHAR(100),
                    address TEXT,
                    emergency_contact_name VARCHAR(100),
                    emergency_contact_phone VARCHAR(50),
                    status VARCHAR(30) NOT NULL DEFAULT 'active',
                    hire_date DATE,
                    leave_date DATE,
                    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
                    job_title_id INTEGER REFERENCES job_titles(id) ON DELETE SET NULL,
                    manager_employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
                """
            )

            cur.execute(
                """
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS english_name VARCHAR(255);
                """
            )

            cur.execute(
                """
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS photo_url TEXT;
                """
            )

            cur.execute(
                """
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
                """
            )

            cur.execute(
                """
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS employee_no VARCHAR(50);
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS employee_movements (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                    movement_type VARCHAR(30) NOT NULL,
                    effective_date DATE NOT NULL,
                    from_department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
                    to_department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
                    from_job_title_id INTEGER REFERENCES job_titles(id) ON DELETE SET NULL,
                    to_job_title_id INTEGER REFERENCES job_titles(id) ON DELETE SET NULL,
                    from_status VARCHAR(30),
                    to_status VARCHAR(30),
                    remark TEXT,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS leave_types (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    is_paid BOOLEAN NOT NULL DEFAULT TRUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                    leave_type_id INTEGER NOT NULL REFERENCES leave_types(id) ON DELETE RESTRICT,
                    start_datetime TIMESTAMP NOT NULL,
                    end_datetime TIMESTAMP NOT NULL,
                    hours NUMERIC(8, 2) NOT NULL DEFAULT 0,
                    reason TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'pending',
                    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    approved_at TIMESTAMP NULL,
                    approval_note TEXT,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS attendance_records (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                    attendance_date DATE NOT NULL,
                    check_in_time TIMESTAMP NULL,
                    check_out_time TIMESTAMP NULL,
                    status VARCHAR(30) NOT NULL DEFAULT 'present',
                    note TEXT,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(employee_id, attendance_date)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    module_name VARCHAR(50) NOT NULL,
                    action_type VARCHAR(30) NOT NULL,
                    target_type VARCHAR(50) NOT NULL,
                    target_id INTEGER,
                    actor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    actor_name VARCHAR(100),
                    summary TEXT,
                    detail_json JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_documents (
                    id SERIAL PRIMARY KEY,
                    doc_no VARCHAR(50) UNIQUE NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    doc_type VARCHAR(50) NOT NULL,
                    applicant_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    applicant_name VARCHAR(100),
                    content TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'draft',
                    current_step INTEGER NOT NULL DEFAULT 0,
                    current_approver_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    submitted_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    rejected_at TIMESTAMP NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_documents (
                    id SERIAL PRIMARY KEY,
                    doc_no VARCHAR(50) UNIQUE NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    doc_type VARCHAR(50) NOT NULL,
                    applicant_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    applicant_name VARCHAR(100),
                    content TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'draft',
                    current_step INTEGER NOT NULL DEFAULT 0,
                    current_approver_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    submitted_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    rejected_at TIMESTAMP NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                ALTER TABLE approval_documents
                ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES approval_templates(id) ON DELETE SET NULL;
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_templates (
                    id SERIAL PRIMARY KEY,
                    template_name VARCHAR(100) NOT NULL UNIQUE,
                    doc_type VARCHAR(50) NOT NULL,
                    title_template VARCHAR(200) NOT NULL,
                    content_template TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                ALTER TABLE approval_templates
                ADD COLUMN IF NOT EXISTS allow_pdf_export BOOLEAN NOT NULL DEFAULT FALSE;
                """
            )

            cur.execute(
                """
                ALTER TABLE approval_templates
                ADD COLUMN IF NOT EXISTS is_fixed_flow BOOLEAN NOT NULL DEFAULT TRUE;
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_template_steps (
                    id SERIAL PRIMARY KEY,
                    template_id INTEGER NOT NULL REFERENCES approval_templates(id) ON DELETE CASCADE,
                    step_no INTEGER NOT NULL,
                    approver_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    approver_name VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(template_id, step_no)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS talents (
                    id SERIAL PRIMARY KEY,
                    stage_name VARCHAR(100) NOT NULL,
                    real_name VARCHAR(100),
                    gender VARCHAR(30),
                    nationality VARCHAR(100),
                    birthday DATE,
                    team_name VARCHAR(100),
                    agency_name VARCHAR(100),
                    instagram_url TEXT,
                    tiktok_url TEXT,
                    youtube_url TEXT,
                    contact_info TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'active',
                    notes TEXT,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS talent_evaluations (
                    id SERIAL PRIMARY KEY,
                    talent_id INTEGER NOT NULL REFERENCES talents(id) ON DELETE CASCADE,
                    report_title VARCHAR(200) NOT NULL,
                    evaluation_date DATE NOT NULL DEFAULT CURRENT_DATE,

                    appearance_score INTEGER NOT NULL DEFAULT 0,
                    performance_score INTEGER NOT NULL DEFAULT 0,
                    social_score INTEGER NOT NULL DEFAULT 0,
                    commercial_score INTEGER NOT NULL DEFAULT 0,
                    team_fit_score INTEGER NOT NULL DEFAULT 0,
                    growth_score INTEGER NOT NULL DEFAULT 0,
                    risk_score INTEGER NOT NULL DEFAULT 0,

                    instagram_followers INTEGER NOT NULL DEFAULT 0,
                    tiktok_followers INTEGER NOT NULL DEFAULT 0,
                    youtube_subscribers INTEGER NOT NULL DEFAULT 0,
                    engagement_rate NUMERIC(6, 2) NOT NULL DEFAULT 0,

                    business_value TEXT,
                    social_analysis TEXT,
                    team_fit_analysis TEXT,
                    signing_review TEXT,
                    investment_model TEXT,
                    executive_notes TEXT,

                    total_score INTEGER NOT NULL DEFAULT 0,
                    grade VARCHAR(5) NOT NULL DEFAULT 'D',
                    status VARCHAR(30) NOT NULL DEFAULT 'draft',

                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

        conn.commit()

    seed_rbac(database_url)
    seed_admin_user(database_url)
    seed_finance_categories(database_url)
    seed_hr_basic_data(database_url)
    seed_approval_templates(database_url)


def seed_rbac(database_url: str) -> None:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            for code, desc in PERMS:
                cur.execute(
                    """
                    INSERT INTO permissions (code, description)
                    VALUES (%s, %s)
                    ON CONFLICT (code) DO UPDATE
                    SET description = EXCLUDED.description
                    """,
                    (code, desc),
                )

            for role_name, role_info in DEFAULT_ROLES.items():
                cur.execute(
                    """
                    INSERT INTO roles (name, description)
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET description = EXCLUDED.description
                    """,
                    (role_name, role_info["description"]),
                )

            for role_name, role_info in DEFAULT_ROLES.items():
                cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
                role_row = cur.fetchone()
                if not role_row:
                    continue

                role_id = role_row["id"]

                for perm_code in role_info["permissions"]:
                    cur.execute("SELECT id FROM permissions WHERE code = %s", (perm_code,))
                    perm_row = cur.fetchone()
                    if not perm_row:
                        continue

                    permission_id = perm_row["id"]

                    cur.execute(
                        """
                        INSERT INTO role_permissions (role_id, permission_id)
                        VALUES (%s, %s)
                        ON CONFLICT (role_id, permission_id) DO NOTHING
                        """,
                        (role_id, permission_id),
                    )

        conn.commit()


def seed_admin_user(database_url: str) -> None:
    import os

    admin_username = os.environ.get("CREATEX_INIT_ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("CREATEX_INIT_ADMIN_PASSWORD", "1234")
    admin_display_name = os.environ.get("CREATEX_INIT_ADMIN_DISPLAY_NAME", "劉建佑")

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (admin_username,))
            user = cur.fetchone()

            if not user:
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, display_name, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (
                        admin_username,
                        generate_password_hash(admin_password),
                        admin_display_name,
                    ),
                )
                user_id = cur.fetchone()["id"]
            else:
                user_id = user["id"]

            cur.execute("SELECT id FROM roles WHERE name = %s", ("Owner",))
            role = cur.fetchone()

            if role:
                cur.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """,
                    (user_id, role["id"]),
                )

        conn.commit()


def get_user_roles(database_url: str, user_id: int) -> list[str]:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    return [row["name"] for row in rows]


def get_user_permissions(database_url: str, user_id: int) -> Set[str]:
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT p.code
                FROM user_roles ur
                JOIN role_permissions rp ON rp.role_id = ur.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = %s
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    return {row["code"] for row in rows}


def get_user_by_username(database_url: str, username: str):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, display_name, is_active
                FROM users
                WHERE username = %s
                """,
                (username,),
            )
            return cur.fetchone()


def get_user_by_id(database_url: str, user_id: int):
    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, display_name, is_active
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            return cur.fetchone()
        
def seed_finance_categories(database_url: str):
    default_categories = [
        ("income", "票務收入", 1),
        ("income", "周邊收入", 2),
        ("income", "贊助收入", 3),
        ("income", "合作分潤", 4),
        ("income", "其他收入", 99),

        ("expense", "活動成本", 1),
        ("expense", "場地費", 2),
        ("expense", "餐飲費", 3),
        ("expense", "設計費", 4),
        ("expense", "交通費", 5),
        ("expense", "住宿費", 6),
        ("expense", "人事費", 7),
        ("expense", "行銷費", 8),
        ("expense", "印刷製作費", 9),
        ("expense", "其他支出", 99),
    ]

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            for category_type, name, sort_order in default_categories:
                cur.execute(
                    """
                    INSERT INTO finance_categories (category_type, name, sort_order, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    ON CONFLICT (category_type, name) DO NOTHING
                    """,
                    (category_type, name, sort_order),
                )
        conn.commit()

def seed_hr_basic_data(database_url: str):
    default_leave_types = [
        ("annual_leave", "特休", True, 1),
        ("sick_leave", "病假", True, 2),
        ("personal_leave", "事假", False, 3),
        ("official_leave", "公假", True, 4),
        ("comp_leave", "補休", True, 5),
        ("unpaid_leave", "無薪假", False, 6),
    ]

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            for code, name, is_paid, sort_order in default_leave_types:
                cur.execute(
                    """
                    INSERT INTO leave_types (code, name, is_paid, sort_order, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (code) DO NOTHING
                    """,
                    (code, name, is_paid, sort_order),
                )
        conn.commit()

def seed_approval_templates(database_url: str):
    default_templates = [
        {
            "template_name": "一般簽呈",
            "doc_type": "general_request",
            "title_template": "一般簽呈申請",
            "content_template": "請填寫申請事由、內容說明、預期效益。",
        },
        {
            "template_name": "請款申請單",
            "doc_type": "payment_request",
            "title_template": "請款申請 - {主題}",
            "content_template": "請填寫請款事由、金額、付款對象、相關附件說明。",
        },
        {
            "template_name": "採購申請單",
            "doc_type": "purchase_request",
            "title_template": "採購申請 - {主題}",
            "content_template": "請填寫採購目的、品項、預算、使用時程。",
        },
        {
            "template_name": "活動預算申請",
            "doc_type": "event_budget",
            "title_template": "活動預算申請 - {活動名稱}",
            "content_template": "請填寫活動名稱、預算內容、收益預估、執行期間。",
        },
    ]

    with get_db(database_url) as conn:
        with conn.cursor() as cur:
            for item in default_templates:
                cur.execute(
                    """
                    INSERT INTO approval_templates (
                        template_name, doc_type, title_template, content_template, is_active
                    )
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (template_name) DO NOTHING
                    """,
                    (
                        item["template_name"],
                        item["doc_type"],
                        item["title_template"],
                        item["content_template"],
                    ),
                )
        conn.commit()