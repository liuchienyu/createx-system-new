from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from decorators import permission_required
from modules.hr.services.movements import movement_type_options, list_movements, create_movement, delete_movement
from modules.hr.services.employees import list_active_employees_basic
from modules.hr.services.departments import list_departments
from modules.hr.services.job_titles import list_job_titles

hr_movements_bp = Blueprint("hr_movements", __name__, url_prefix="/hr/movements")


@hr_movements_bp.route("")
@login_required
@permission_required("view_employee_movements")
def index():
    database_url = current_app.config["DATABASE_URL"]
    movement_type = (request.args.get("movement_type") or "").strip()
    return render_template(
        "hr/employee_movements_index.html",
        movements=list_movements(database_url, movement_type),
        movement_type=movement_type,
        movement_types=movement_type_options(),
    )


@hr_movements_bp.route("/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_employee_movements")
def create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        employee_id = (request.form.get("employee_id") or "").strip()
        movement_type = (request.form.get("movement_type") or "").strip()
        effective_date = (request.form.get("effective_date") or "").strip()

        if not employee_id or not movement_type or not effective_date:
            flash("請填寫必要欄位", "danger")
            return redirect(url_for("hr_movements.create"))

        data = {
            "employee_id": int(employee_id),
            "movement_type": movement_type,
            "effective_date": effective_date,
            "to_department_id": int(request.form.get("to_department_id")) if (request.form.get("to_department_id") or "").strip() else None,
            "to_job_title_id": int(request.form.get("to_job_title_id")) if (request.form.get("to_job_title_id") or "").strip() else None,
            "to_status": (request.form.get("to_status") or "").strip() or None,
            "remark": (request.form.get("remark") or "").strip() or None,
            "created_by": int(current_user.id),
        }

        create_movement(database_url, data)
        flash("任用異動建立成功", "success")
        return redirect(url_for("hr_movements.index"))

    return render_template(
        "hr/employee_movement_create.html",
        employees=list_active_employees_basic(database_url),
        departments=list_departments(database_url, True),
        job_titles=list_job_titles(database_url, True),
        movement_types=movement_type_options(),
        selected_employee=request.args.get("employee_id") or "",
    )


@hr_movements_bp.route("/<int:movement_id>/delete", methods=["POST"])
@login_required
@permission_required("delete_employee_movements")
def delete(movement_id: int):
    database_url = current_app.config["DATABASE_URL"]
    delete_movement(database_url, movement_id)
    flash("任用異動紀錄已刪除", "success")
    return redirect(url_for("hr_movements.index"))