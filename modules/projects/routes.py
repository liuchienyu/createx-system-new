from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required

from decorators import permission_required
from modules.projects.services import (
    list_projects,
    get_project,
    create_project,
    update_project,
    toggle_project_active,
    get_project_finance_summary,
    get_project_finance_records,
    get_project_ar_ap_records,
    get_project_profit_report,
)

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/projects")
@login_required
@permission_required("view_projects")
def project_index():
    database_url = current_app.config["DATABASE_URL"]
    is_active = (request.args.get("is_active") or "").strip()

    projects = list_projects(database_url, is_active)

    enriched_projects = []
    for project in projects:
        summary = get_project_finance_summary(database_url, project["id"])
        enriched_projects.append({
            **project,
            **summary,
        })

    return render_template(
        "projects/index.html",
        projects=enriched_projects,
        is_active=is_active,
    )


@projects_bp.route("/projects/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_projects")
def project_create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("請輸入專案名稱", "danger")
            return redirect(url_for("projects.project_create"))
        
        if start_date and end_date and end_date < start_date:
            flash("結束日期不可早於開始日期", "danger")
            return redirect(url_for("projects.project_create"))

        create_project(
            database_url=database_url,
            name=name,
            description=description,
            start_date=start_date or None,
            end_date=end_date or None,
            is_active=is_active,
        )

        flash("專案建立成功", "success")
        return redirect(url_for("projects.project_index"))

    return render_template("projects/create.html")


@projects_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_projects")
def project_edit(project_id: int):
    database_url = current_app.config["DATABASE_URL"]
    project = get_project(database_url, project_id)

    if not project:
        abort(404)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("請輸入專案名稱", "danger")
            return redirect(url_for("projects.project_edit", project_id=project_id))
        
        if start_date and end_date and end_date < start_date:
            flash("結束日期不可早於開始日期", "danger")
            return redirect(url_for("projects.project_edit", project_id=project_id))

        update_project(
            database_url=database_url,
            project_id=project_id,
            name=name,
            description=description,
            start_date=start_date or None,
            end_date=end_date or None,
            is_active=is_active,
        )

        flash("專案更新成功", "success")
        return redirect(url_for("projects.project_index"))

    return render_template("projects/edit.html", project=project)


@projects_bp.route("/projects/<int:project_id>/toggle-active", methods=["POST"])
@login_required
@permission_required("edit_projects")
def project_toggle_active(project_id: int):
    database_url = current_app.config["DATABASE_URL"]
    project = get_project(database_url, project_id)

    if not project:
        abort(404)

    new_active = not project["is_active"]
    toggle_project_active(database_url, project_id, new_active)

    flash("專案狀態已更新", "success")
    return redirect(url_for("projects.project_index"))


@projects_bp.route("/projects/<int:project_id>")
@login_required
@permission_required("view_projects")
def project_detail(project_id: int):
    database_url = current_app.config["DATABASE_URL"]
    project = get_project(database_url, project_id)

    if not project:
        abort(404)

    summary = get_project_finance_summary(database_url, project_id)
    finance_records = get_project_finance_records(database_url, project_id)
    ar_ap_records = get_project_ar_ap_records(database_url, project_id)

    return render_template(
        "projects/detail.html",
        project=project,
        summary=summary,
        finance_records=finance_records,
        ar_ap_records=ar_ap_records,
    )


@projects_bp.route("/projects/<int:project_id>/profit-report")
@login_required
@permission_required("view_projects")
def project_profit_report(project_id: int):
    database_url = current_app.config["DATABASE_URL"]
    project = get_project(database_url, project_id)

    if not project:
        abort(404)

    report = get_project_profit_report(database_url, project_id)

    return render_template(
        "projects/profit_report.html",
        project=project,
        report=report,
    )