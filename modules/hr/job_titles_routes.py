from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required
from decorators import permission_required
from modules.hr.services.job_titles import (
    list_job_titles, get_job_title, create_job_title, update_job_title,
    disable_job_title, active_employee_count_by_job_title,
)

hr_job_titles_bp = Blueprint("hr_job_titles", __name__, url_prefix="/hr/job-titles")


@hr_job_titles_bp.route("")
@login_required
@permission_required("view_job_titles")
def index():
    database_url = current_app.config["DATABASE_URL"]
    active_filter = (request.args.get("is_active") or "").strip()
    job_titles = list_job_titles(database_url, active_filter)
    return render_template(
        "hr/job_titles_index.html",
        job_titles=job_titles,
        active_filter=active_filter,
    )

@hr_job_titles_bp.route("/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_job_titles")
def create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        level = int((request.form.get("level") or "1").strip())
        sort_order = int((request.form.get("sort_order") or "0").strip())
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("請輸入職稱名稱", "danger")
            return redirect(url_for("hr_job_titles.create"))

        create_job_title(database_url, name, level, sort_order, is_active)
        flash("職稱建立成功", "success")
        return redirect(url_for("hr_job_titles.index"))

    return render_template("hr/job_title_create.html")


@hr_job_titles_bp.route("/<int:title_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_job_titles")
def edit(title_id: int):
    database_url = current_app.config["DATABASE_URL"]
    job_title = get_job_title(database_url, title_id)
    if not job_title:
        abort(404)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        level = int((request.form.get("level") or "1").strip())
        sort_order = int((request.form.get("sort_order") or "0").strip())
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("請輸入職稱名稱", "danger")
            return redirect(url_for("hr_job_titles.edit", title_id=title_id))

        update_job_title(database_url, title_id, name, level, sort_order, is_active)
        flash("職稱更新成功", "success")
        return redirect(url_for("hr_job_titles.index"))

    return render_template("hr/job_title_edit.html", job_title=job_title)


@hr_job_titles_bp.route("/<int:title_id>/disable", methods=["POST"])
@login_required
@permission_required("delete_job_titles")
def disable(title_id: int):
    database_url = current_app.config["DATABASE_URL"]
    job_title = get_job_title(database_url, title_id)
    if not job_title:
        abort(404)

    if active_employee_count_by_job_title(database_url, title_id) > 0:
        flash("此職稱仍有在職/留停員工，不可停用", "danger")
        return redirect(url_for("hr_job_titles.index"))

    disable_job_title(database_url, title_id)
    flash("職稱已停用", "success")
    return redirect(url_for("hr_job_titles.index"))