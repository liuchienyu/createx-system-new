from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required
from decorators import permission_required
from modules.hr.services.employees import (
    generate_employee_no, list_employees, get_employee, list_active_employees_basic,
    list_available_users, create_employee, update_employee, archive_employee,
    get_employee_movements, get_employee_leave_requests, get_employee_attendance_records,
)
from modules.hr.services.departments import list_departments
from modules.hr.services.job_titles import list_job_titles

hr_employees_bp = Blueprint("hr_employees", __name__, url_prefix="/hr/employees")


@hr_employees_bp.route("")
@login_required
@permission_required("view_hr")
def index():
    database_url = current_app.config["DATABASE_URL"]
    status = (request.args.get("status") or "").strip()
    employees = list_employees(database_url, status)
    return render_template("hr/employees_index.html", employees=employees, status=status)


@hr_employees_bp.route("/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_hr")
def create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        user_id = (request.form.get("user_id") or "").strip()
        data = {
            "user_id": int(user_id) if user_id else None,
            "employee_no": (request.form.get("employee_no") or "").strip(),
            "name": (request.form.get("name") or "").strip(),
            "english_name": (request.form.get("english_name") or "").strip() or None,
            "nickname": (request.form.get("nickname") or "").strip() or None,
            "gender": (request.form.get("gender") or "").strip() or None,
            "birthday": (request.form.get("birthday") or "").strip() or None,
            "phone": (request.form.get("phone") or "").strip() or None,
            "email": (request.form.get("email") or "").strip() or None,
            "address": (request.form.get("address") or "").strip() or None,
            "emergency_contact_name": (request.form.get("emergency_contact_name") or "").strip() or None,
            "emergency_contact_phone": (request.form.get("emergency_contact_phone") or "").strip() or None,
            "status": (request.form.get("status") or "").strip() or "active",
            "hire_date": (request.form.get("hire_date") or "").strip() or None,
            "leave_date": (request.form.get("leave_date") or "").strip() or None,
            "department_id": int(request.form.get("department_id")) if (request.form.get("department_id") or "").strip() else None,
            "job_title_id": int(request.form.get("job_title_id")) if (request.form.get("job_title_id") or "").strip() else None,
            "manager_employee_id": int(request.form.get("manager_employee_id")) if (request.form.get("manager_employee_id") or "").strip() else None,
            "notes": (request.form.get("notes") or "").strip() or None,
        }

        if not data["employee_no"]:
            data["employee_no"] = generate_employee_no(database_url)

        if not data["name"]:
            flash("請輸入姓名", "danger")
            return redirect(url_for("hr_employees.create"))

        create_employee(database_url, data)
        flash("員工資料建立成功", "success")
        return redirect(url_for("hr_employees.index"))

    return render_template(
        "hr/employee_create.html",
        suggested_employee_no=generate_employee_no(database_url),
        available_users=list_available_users(database_url),
        departments=list_departments(database_url, True),
        job_titles=list_job_titles(database_url, True),
        manager_employees=list_active_employees_basic(database_url),
    )


@hr_employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_hr")
def edit(employee_id: int):
    database_url = current_app.config["DATABASE_URL"]
    employee = get_employee(database_url, employee_id)

    if not employee:
        abort(404)

    if request.method == "POST":
        user_id = (request.form.get("user_id") or "").strip()
        data = {
            "user_id": int(user_id) if user_id else None,
            "employee_no": (request.form.get("employee_no") or "").strip(),
            "name": (request.form.get("name") or "").strip(),
            "english_name": (request.form.get("english_name") or "").strip() or None,
            "nickname": (request.form.get("nickname") or "").strip() or None,
            "gender": (request.form.get("gender") or "").strip() or None,
            "birthday": (request.form.get("birthday") or "").strip() or None,
            "phone": (request.form.get("phone") or "").strip() or None,
            "email": (request.form.get("email") or "").strip() or None,
            "address": (request.form.get("address") or "").strip() or None,
            "emergency_contact_name": (request.form.get("emergency_contact_name") or "").strip() or None,
            "emergency_contact_phone": (request.form.get("emergency_contact_phone") or "").strip() or None,
            "status": (request.form.get("status") or "").strip() or "active",
            "hire_date": (request.form.get("hire_date") or "").strip() or None,
            "leave_date": (request.form.get("leave_date") or "").strip() or None,
            "department_id": int(request.form.get("department_id")) if (request.form.get("department_id") or "").strip() else None,
            "job_title_id": int(request.form.get("job_title_id")) if (request.form.get("job_title_id") or "").strip() else None,
            "manager_employee_id": int(request.form.get("manager_employee_id")) if (request.form.get("manager_employee_id") or "").strip() else None,
            "notes": (request.form.get("notes") or "").strip() or None,
        }

        if not data["name"]:
            flash("請輸入姓名", "danger")
            return redirect(url_for("hr_employees.edit", employee_id=employee_id))

        update_employee(database_url, employee_id, data)
        flash("員工資料更新成功", "success")
        return redirect(url_for("hr_employees.index"))

    return render_template(
        "hr/employee_edit.html",
        employee=employee,
        available_users=list_available_users(database_url, employee["user_id"]),
        departments=list_departments(database_url, True),
        job_titles=list_job_titles(database_url, True),
        manager_employees=[e for e in list_active_employees_basic(database_url) if e["id"] != employee_id],
    )


@hr_employees_bp.route("/<int:employee_id>")
@login_required
@permission_required("view_hr")
def detail(employee_id: int):
    database_url = current_app.config["DATABASE_URL"]
    employee = get_employee(database_url, employee_id)
    if not employee:
        abort(404)

    return render_template(
        "hr/employee_detail.html",
        employee=employee,
        movements=get_employee_movements(database_url, employee_id),
        leave_requests=get_employee_leave_requests(database_url, employee_id),
        attendance_records=get_employee_attendance_records(database_url, employee_id),
    )


@hr_employees_bp.route("/<int:employee_id>/archive", methods=["POST"])
@login_required
@permission_required("delete_hr")
def archive(employee_id: int):
    database_url = current_app.config["DATABASE_URL"]
    employee = get_employee(database_url, employee_id)
    if not employee:
        abort(404)

    archive_employee(database_url, employee_id)
    flash("員工資料已封存", "success")
    return redirect(url_for("hr_employees.index"))