from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from decorators import permission_required
from modules.hr.services.attendance import (
    list_attendance_records, create_manual_attendance, delete_attendance_record,
    get_employee_by_user_id, get_today_attendance, clock_in, clock_out,
)
from modules.hr.services.employees import list_active_employees_basic

hr_attendance_bp = Blueprint("hr_attendance", __name__, url_prefix="/hr")
TW = ZoneInfo("Asia/Taipei")


@hr_attendance_bp.route("/attendance")
@login_required
@permission_required("view_attendance")
def attendance_index():
    database_url = current_app.config["DATABASE_URL"]
    employee_id = (request.args.get("employee_id") or "").strip()
    attendance_date = (request.args.get("attendance_date") or "").strip()

    return render_template(
        "hr/attendance_index.html",
        attendance_records=list_attendance_records(database_url, employee_id, attendance_date),
        employees=list_active_employees_basic(database_url),
        employee_id=employee_id,
        attendance_date=attendance_date,
    )


@hr_attendance_bp.route("/attendance/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_attendance")
def attendance_manual_create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        employee_id = (request.form.get("employee_id") or "").strip()
        attendance_date = (request.form.get("attendance_date") or "").strip()

        if not employee_id or not attendance_date:
            flash("請填寫必要欄位", "danger")
            return redirect(url_for("hr_attendance.attendance_manual_create"))

        create_manual_attendance(
            database_url,
            {
                "employee_id": int(employee_id),
                "attendance_date": attendance_date,
                "check_in_time": ((request.form.get("check_in_time") or "").strip().replace("T", " ") or None),
                "check_out_time": ((request.form.get("check_out_time") or "").strip().replace("T", " ") or None),
                "status": (request.form.get("status") or "").strip() or "present",
                "note": (request.form.get("note") or "").strip() or None,
                "created_by": int(current_user.id),
            },
        )
        flash("出勤紀錄已建立 / 更新", "success")
        return redirect(url_for("hr_attendance.attendance_index"))

    return render_template("hr/attendance_manual_create.html", employees=list_active_employees_basic(database_url))


@hr_attendance_bp.route("/attendance/<int:record_id>/delete", methods=["POST"])
@login_required
@permission_required("delete_attendance")
def attendance_delete(record_id: int):
    database_url = current_app.config["DATABASE_URL"]
    delete_attendance_record(database_url, record_id)
    flash("出勤紀錄已刪除", "success")
    return redirect(url_for("hr_attendance.attendance_index"))


@hr_attendance_bp.route("/my-clock", methods=["GET", "POST"])
@login_required
@permission_required("clock_attendance")
def my_clock():
    database_url = current_app.config["DATABASE_URL"]
    employee = get_employee_by_user_id(database_url, int(current_user.id))

    if not employee:
        flash("目前帳號尚未綁定員工資料", "danger")
        return redirect(url_for("dashboard.index"))

    now_dt = datetime.now(TW).replace(tzinfo=None)
    today = now_dt.date()
    today_record = get_today_attendance(database_url, employee["id"], today)

    if request.method == "POST":
        action = (request.form.get("action") or "").strip()

        if action == "clock_in":
            if today_record and today_record["check_in_time"]:
                flash("今天已完成上班打卡", "warning")
                return redirect(url_for("hr_attendance.my_clock"))

            clock_in(database_url, employee["id"], today, now_dt, int(current_user.id))
            flash("上班打卡成功", "success")
            return redirect(url_for("hr_attendance.my_clock"))

        if action == "clock_out":
            if not today_record or not today_record["check_in_time"]:
                flash("請先進行上班打卡", "danger")
                return redirect(url_for("hr_attendance.my_clock"))

            if today_record["check_out_time"]:
                flash("今天已完成下班打卡", "warning")
                return redirect(url_for("hr_attendance.my_clock"))

            clock_out(database_url, employee["id"], today, now_dt)
            flash("下班打卡成功", "success")
            return redirect(url_for("hr_attendance.my_clock"))

    today_record = get_today_attendance(database_url, employee["id"], today)

    return render_template(
        "hr/my_clock.html",
        employee=employee,
        current_time=now_dt,
        today_record=today_record,
    )