from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required
from decorators import permission_required
from modules.hr.services.departments import (
    list_departments, get_department, create_department, update_department,
    disable_department, active_employee_count_by_department,
)

hr_departments_bp = Blueprint("hr_departments", __name__, url_prefix="/hr/departments")


@hr_departments_bp.route("")
@login_required
@permission_required("view_departments")
def index():
    database_url = current_app.config["DATABASE_URL"]
    departments = list_departments(database_url, False)
    return render_template("hr/departments_index.html", departments=departments)


@hr_departments_bp.route("/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_departments")
def create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        parent_id = (request.form.get("parent_id") or "").strip()
        sort_order = int((request.form.get("sort_order") or "0").strip())
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("請輸入部門名稱", "danger")
            return redirect(url_for("hr_departments.create"))

        create_department(database_url, name, int(parent_id) if parent_id else None, sort_order, is_active)
        flash("部門建立成功", "success")
        return redirect(url_for("hr_departments.index"))

    return render_template("hr/department_create.html", parent_departments=list_departments(database_url, True))


@hr_departments_bp.route("/<int:department_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_departments")
def edit(department_id: int):
    database_url = current_app.config["DATABASE_URL"]
    department = get_department(database_url, department_id)
    if not department:
        abort(404)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        parent_id = (request.form.get("parent_id") or "").strip()
        sort_order = int((request.form.get("sort_order") or "0").strip())
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("請輸入部門名稱", "danger")
            return redirect(url_for("hr_departments.edit", department_id=department_id))

        update_department(database_url, department_id, name, int(parent_id) if parent_id else None, sort_order, is_active)
        flash("部門更新成功", "success")
        return redirect(url_for("hr_departments.index"))

    return render_template(
        "hr/department_edit.html",
        department=department,
        parent_departments=[d for d in list_departments(database_url, False) if d["id"] != department_id],
    )


@hr_departments_bp.route("/<int:department_id>/disable", methods=["POST"])
@login_required
@permission_required("delete_departments")
def disable(department_id: int):
    database_url = current_app.config["DATABASE_URL"]
    department = get_department(database_url, department_id)
    if not department:
        abort(404)

    if active_employee_count_by_department(database_url, department_id) > 0:
        flash("此部門仍有在職/留停員工，不可停用", "danger")
        return redirect(url_for("hr_departments.index"))

    disable_department(database_url, department_id)
    flash("部門已停用", "success")
    return redirect(url_for("hr_departments.index"))