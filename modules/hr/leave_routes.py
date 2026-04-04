from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from decorators import permission_required
from modules.hr.services.leave import (
    get_leave_types, calculate_leave_hours, list_leave_requests, get_leave_request,
    create_leave_request, approve_leave_request, delete_leave_request, disable_leave_type,
)
from modules.hr.services.employees import list_active_employees_basic

hr_leave_bp = Blueprint("hr_leave", __name__, url_prefix="/hr")


@hr_leave_bp.route("/leave-types")
@login_required
@permission_required("view_leave")
def leave_types_index():
    database_url = current_app.config["DATABASE_URL"]
    active_filter = (request.args.get("is_active") or "").strip()
    leave_types = get_leave_types(database_url, active_filter if active_filter else "")
    return render_template(
        "hr/leave_types_index.html",
        leave_types=leave_types,
        active_filter=active_filter,
    )

@hr_leave_bp.route("/leave-requests/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_leave")
def leave_request_create():
    database_url = current_app.config["DATABASE_URL"]
    selected_employee_id = (request.args.get("employee_id") or "").strip()

    if request.method == "POST":
        employee_id = (request.form.get("employee_id") or "").strip()
        leave_type_id = (request.form.get("leave_type_id") or "").strip()
        start_datetime = (request.form.get("start_datetime") or "").strip()
        end_datetime = (request.form.get("end_datetime") or "").strip()
        reason = (request.form.get("reason") or "").strip()

        if not employee_id or not leave_type_id or not start_datetime or not end_datetime:
            flash("請填寫必要欄位", "danger")
            return redirect(url_for("hr_leave.leave_request_create"))

        hours = calculate_leave_hours(start_datetime, end_datetime)
        if hours <= 0:
            flash("請假時間區間錯誤", "danger")
            return redirect(url_for("hr_leave.leave_request_create"))

        create_leave_request(
            database_url,
            {
                "employee_id": int(employee_id),
                "leave_type_id": int(leave_type_id),
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "hours": hours,
                "reason": reason,
                "created_by": int(current_user.id),
            },
        )
        flash("請假申請建立成功", "success")
        return redirect(url_for("hr_leave.leave_requests_index"))

    return render_template(
        "hr/leave_request_create.html",
        employees=list_active_employees_basic(database_url),
        leave_types=get_leave_types(database_url, "true"),
        selected_employee_id=selected_employee_id,
    )


@hr_leave_bp.route("/leave-requests/<int:request_id>", methods=["GET", "POST"])
@login_required
@permission_required("view_leave")
def leave_request_detail(request_id: int):
    database_url = current_app.config["DATABASE_URL"]
    leave_request = get_leave_request(database_url, request_id)
    if not leave_request:
        abort(404)

    if request.method == "POST":
        if not current_user.has_permission("approve_leave"):
            flash("你沒有審核權限", "danger")
            return redirect(url_for("hr_leave.leave_request_detail", request_id=request_id))

        action = (request.form.get("action") or "").strip()
        approval_note = (request.form.get("approval_note") or "").strip()

        if leave_request["status"] != "pending":
            flash("這筆請假單已處理過", "warning")
            return redirect(url_for("hr_leave.leave_request_detail", request_id=request_id))

        if action not in ["approved", "rejected", "cancelled"]:
            flash("不合法的操作", "danger")
            return redirect(url_for("hr_leave.leave_request_detail", request_id=request_id))

        approve_leave_request(database_url, request_id, action, approval_note, int(current_user.id))
        flash("請假單狀態已更新", "success")
        return redirect(url_for("hr_leave.leave_request_detail", request_id=request_id))

    return render_template("hr/leave_request_detail.html", leave_request=leave_request)


@hr_leave_bp.route("/leave-requests/<int:request_id>/delete", methods=["POST"])
@login_required
@permission_required("delete_leave")
def leave_request_delete(request_id: int):
    database_url = current_app.config["DATABASE_URL"]
    leave_request = get_leave_request(database_url, request_id)
    if not leave_request:
        abort(404)

    if leave_request["status"] != "pending":
        flash("只有待審核請假單可刪除", "danger")
        return redirect(url_for("hr_leave.leave_requests_index"))

    delete_leave_request(database_url, request_id)
    flash("請假申請已刪除", "success")
    return redirect(url_for("hr_leave.leave_requests_index"))


@hr_leave_bp.route("/leave-types")
@login_required
@permission_required("view_leave")
def leave_types_index():
    database_url = current_app.config["DATABASE_URL"]
    return render_template("hr/leave_types_index.html", leave_types=get_leave_types(database_url, False))


@hr_leave_bp.route("/leave-types/<int:type_id>/disable", methods=["POST"])
@login_required
@permission_required("delete_leave_types")
def leave_type_disable(type_id: int):
    database_url = current_app.config["DATABASE_URL"]
    disable_leave_type(database_url, type_id)
    flash("請假類型已停用", "success")
    return redirect(url_for("hr_leave.leave_types_index"))