from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user

from decorators import permission_required
from modules.approvals.services import (
    generate_doc_no,
    list_documents,
    get_document,
    get_document_steps,
    list_approver_users,
    create_document,
    submit_document,
    list_my_pending_documents,
    approve_document,
    create_document_from_template,
    update_document_draft,
)

from flask import send_file
from modules.approvals.template_services import (
    list_approval_templates,
    get_approval_template,
    get_template_steps,
    list_approval_templates,
    create_approval_template,
    disable_approval_template,
    update_approval_template,    
)
from modules.approvals.pdf_services import build_approval_pdf

approvals_bp = Blueprint("approvals", __name__, url_prefix="/approvals")


@approvals_bp.route("")
@login_required
@permission_required("view_approvals")
def index():
    database_url = current_app.config["DATABASE_URL"]
    status = (request.args.get("status") or "").strip()
    applicant_user_id = (request.args.get("applicant_user_id") or "").strip()

    documents = list_documents(database_url, status, applicant_user_id)

    return render_template(
        "approvals/index.html",
        documents=documents,
        status=status,
        applicant_user_id=applicant_user_id,
    )


@approvals_bp.route("/create", methods=["GET", "POST"])
@login_required
@permission_required("edit_approvals")
def create():
    database_url = current_app.config["DATABASE_URL"]
    approver_users = list_approver_users(database_url)
    templates = list_approval_templates(database_url, "true")

    if request.method == "POST":
        template_id = (request.form.get("template_id") or "").strip()
        title = (request.form.get("title") or "").strip()
        doc_type = (request.form.get("doc_type") or "").strip()
        content = (request.form.get("content") or "").strip()

        if template_id:
            document_id, message = create_document_from_template(
                database_url,
                {
                    "template_id": int(template_id),
                    "doc_no": generate_doc_no(database_url),
                    "title": title,
                    "content": content,
                    "applicant_user_id": int(current_user.id),
                    "applicant_name": current_user.display_name,
                },
            )

            if not document_id:
                flash(message, "danger")
                return redirect(url_for("approvals.create"))

            flash(message, "success")
            return redirect(url_for("approvals.detail", document_id=document_id))

        approver_1 = (request.form.get("approver_1") or "").strip()
        approver_2 = (request.form.get("approver_2") or "").strip()
        approver_3 = (request.form.get("approver_3") or "").strip()

        if not title:
            flash("請輸入公文標題", "danger")
            return redirect(url_for("approvals.create"))

        if not doc_type:
            flash("請輸入公文類型", "danger")
            return redirect(url_for("approvals.create"))

        selected_ids = [x for x in [approver_1, approver_2, approver_3] if x]
        if not selected_ids:
            flash("至少要設定一位簽核人", "danger")
            return redirect(url_for("approvals.create"))

        approver_map = {str(u["id"]): u for u in approver_users}

        steps = []
        for approver_id in selected_ids:
            user = approver_map.get(approver_id)
            if not user:
                flash("簽核人不存在", "danger")
                return redirect(url_for("approvals.create"))

            steps.append(
                {
                    "approver_user_id": user["id"],
                    "approver_name": user["display_name"] or user["username"],
                }
            )

        document_id = create_document(
            database_url,
            {
                "doc_no": generate_doc_no(database_url),
                "title": title,
                "doc_type": doc_type,
                "applicant_user_id": int(current_user.id),
                "applicant_name": current_user.display_name,
                "content": content,
                "steps": steps,
            },
        )

        flash("公文草稿建立成功", "success")
        return redirect(url_for("approvals.detail", document_id=document_id))

    return render_template(
        "approvals/create.html",
        suggested_doc_no=generate_doc_no(database_url),
        approver_users=approver_users,
        templates=templates,
    )

@approvals_bp.route("/templates")
@login_required
@permission_required("manage_approval_templates")
def templates_index():
    database_url = current_app.config["DATABASE_URL"]
    active_filter = (request.args.get("is_active") or "").strip()
    templates = list_approval_templates(database_url, active_filter)
    return render_template(
        "approvals/templates_index.html",
        templates=templates,
        active_filter=active_filter,
    )

@approvals_bp.route("/templates/create", methods=["GET", "POST"])
@login_required
@permission_required("manage_approval_templates")
def templates_create():
    database_url = current_app.config["DATABASE_URL"]
    approver_users = list_approver_users(database_url)

    if request.method == "POST":
        template_name = (request.form.get("template_name") or "").strip()
        doc_type = (request.form.get("doc_type") or "").strip()
        title_template = (request.form.get("title_template") or "").strip()
        content_template = (request.form.get("content_template") or "").strip()
        is_active = request.form.get("is_active") == "on"

        approver_1 = (request.form.get("approver_1") or "").strip()
        approver_2 = (request.form.get("approver_2") or "").strip()
        approver_3 = (request.form.get("approver_3") or "").strip()

        if not template_name:
            flash("請輸入模板名稱", "danger")
            return redirect(url_for("approvals.templates_create"))

        if not doc_type:
            flash("請輸入公文類型", "danger")
            return redirect(url_for("approvals.templates_create"))

        if not title_template:
            flash("請輸入標題模板", "danger")
            return redirect(url_for("approvals.templates_create"))

        selected_ids = [x for x in [approver_1, approver_2, approver_3] if x]
        if not selected_ids:
            flash("至少要設定一位簽核人", "danger")
            return redirect(url_for("approvals.templates_create"))

        approver_map = {str(u["id"]): u for u in approver_users}
        steps = []
        for approver_id in selected_ids:
            user = approver_map.get(approver_id)
            if not user:
                flash("簽核人不存在", "danger")
                return redirect(url_for("approvals.templates_create"))

            steps.append(
                {
                    "approver_user_id": user["id"],
                    "approver_name": user["display_name"] or user["username"],
                }
            )

        create_approval_template(
            database_url,
            {
                "template_name": template_name,
                "doc_type": doc_type,
                "title_template": title_template,
                "content_template": content_template,
                "is_active": is_active,
                "steps": steps,
            },
        )

        flash("公文模板建立成功", "success")
        return redirect(url_for("approvals.templates_index"))

    return render_template("approvals/create.html", mode="template", approver_users=approver_users)

@approvals_bp.route("/templates/<int:template_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("manage_approval_templates")
def templates_edit(template_id: int):
    database_url = current_app.config["DATABASE_URL"]
    template = get_approval_template(database_url, template_id)

    if not template:
        abort(404)

    approver_users = list_approver_users(database_url)
    template_steps = get_template_steps(database_url, template_id)

    if request.method == "POST":
        template_name = (request.form.get("template_name") or "").strip()
        doc_type = (request.form.get("doc_type") or "").strip()
        title_template = (request.form.get("title_template") or "").strip()
        content_template = (request.form.get("content_template") or "").strip()
        is_active = request.form.get("is_active") == "on"
        allow_pdf_export = request.form.get("allow_pdf_export") == "on"
        is_fixed_flow = request.form.get("is_fixed_flow") == "on"

        approver_1 = (request.form.get("approver_1") or "").strip()
        approver_2 = (request.form.get("approver_2") or "").strip()
        approver_3 = (request.form.get("approver_3") or "").strip()

        if not template_name:
            flash("請輸入模板名稱", "danger")
            return redirect(url_for("approvals.templates_edit", template_id=template_id))

        if not doc_type:
            flash("請輸入公文類型", "danger")
            return redirect(url_for("approvals.templates_edit", template_id=template_id))

        if not title_template:
            flash("請輸入標題模板", "danger")
            return redirect(url_for("approvals.templates_edit", template_id=template_id))

        selected_ids = [x for x in [approver_1, approver_2, approver_3] if x]
        if not selected_ids:
            flash("至少要設定一位簽核人", "danger")
            return redirect(url_for("approvals.templates_edit", template_id=template_id))

        approver_map = {str(u["id"]): u for u in approver_users}
        steps = []
        for approver_id in selected_ids:
            user = approver_map.get(approver_id)
            if not user:
                flash("簽核人不存在", "danger")
                return redirect(url_for("approvals.templates_edit", template_id=template_id))

            steps.append(
                {
                    "approver_user_id": user["id"],
                    "approver_name": user["display_name"] or user["username"],
                }
            )

        update_approval_template(
            database_url,
            template_id,
            {
                "template_name": template_name,
                "doc_type": doc_type,
                "title_template": title_template,
                "content_template": content_template,
                "is_active": is_active,
                "allow_pdf_export": allow_pdf_export,
                "is_fixed_flow": is_fixed_flow,
                "steps": steps,
            },
        )

        flash("模板更新成功", "success")
        return redirect(url_for("approvals.templates_index"))

    return render_template(
        "approvals/template_edit.html",
        template=template,
        approver_users=approver_users,
        template_steps=template_steps,
    )

@approvals_bp.route("/templates/<int:template_id>/disable", methods=["POST"])
@login_required
@permission_required("manage_approval_templates")
def templates_disable(template_id: int):
    database_url = current_app.config["DATABASE_URL"]
    template = get_approval_template(database_url, template_id)

    if not template:
        abort(404)

    disable_approval_template(database_url, template_id)
    flash("模板已停用", "success")
    return redirect(url_for("approvals.templates_index"))

@approvals_bp.route("/<int:document_id>")
@login_required
@permission_required("view_approvals")
def detail(document_id: int):
    database_url = current_app.config["DATABASE_URL"]
    document = get_document(database_url, document_id)

    if not document:
        abort(404)

    steps = get_document_steps(database_url, document_id)

    can_submit = (
        current_user.has_permission("edit_approvals")
        and document["status"] == "draft"
        and document["applicant_user_id"] == int(current_user.id)
    )

    can_approve = (
        current_user.has_permission("approve_documents")
        and document["status"] == "pending"
        and document["current_approver_user_id"] == int(current_user.id)
    )

    return render_template(
        "approvals/detail.html",
        document=document,
        steps=steps,
        can_submit=can_submit,
        can_approve=can_approve,
    )

@approvals_bp.route("/<int:document_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit_approvals")
def edit(document_id: int):
    database_url = current_app.config["DATABASE_URL"]
    document = get_document(database_url, document_id)

    if not document:
        abort(404)

    if document["status"] != "draft":
        flash("只有草稿狀態可編輯", "danger")
        return redirect(url_for("approvals.detail", document_id=document_id))

    if document["applicant_user_id"] != int(current_user.id):
        flash("只能編輯自己建立的草稿", "danger")
        return redirect(url_for("approvals.detail", document_id=document_id))

    approver_users = list_approver_users(database_url)
    steps = get_document_steps(database_url, document_id)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        doc_type = (request.form.get("doc_type") or "").strip()
        content = (request.form.get("content") or "").strip()

        if not title:
            flash("請輸入公文標題", "danger")
            return redirect(url_for("approvals.edit", document_id=document_id))

        if not doc_type:
            flash("請輸入公文類型", "danger")
            return redirect(url_for("approvals.edit", document_id=document_id))

        is_fixed_flow = bool(document.get("is_fixed_flow"))

        step_data = []
        if not is_fixed_flow:
            approver_1 = (request.form.get("approver_1") or "").strip()
            approver_2 = (request.form.get("approver_2") or "").strip()
            approver_3 = (request.form.get("approver_3") or "").strip()

            selected_ids = [x for x in [approver_1, approver_2, approver_3] if x]
            if not selected_ids:
                flash("至少要設定一位簽核人", "danger")
                return redirect(url_for("approvals.edit", document_id=document_id))

            approver_map = {str(u["id"]): u for u in approver_users}
            for approver_id in selected_ids:
                user = approver_map.get(approver_id)
                if not user:
                    flash("簽核人不存在", "danger")
                    return redirect(url_for("approvals.edit", document_id=document_id))

                step_data.append(
                    {
                        "approver_user_id": user["id"],
                        "approver_name": user["display_name"] or user["username"],
                    }
                )

        ok, message = update_document_draft(
            database_url,
            document_id,
            {
                "title": title,
                "doc_type": doc_type,
                "content": content,
                "is_fixed_flow": is_fixed_flow,
                "steps": step_data,
            },
        )

        flash(message, "success" if ok else "danger")
        return redirect(url_for("approvals.detail", document_id=document_id))

    return render_template(
        "approvals/edit.html",
        document=document,
        approver_users=approver_users,
        steps=steps,
    )

@approvals_bp.route("/<int:document_id>/export-pdf")
@login_required
@permission_required("view_approvals")
def export_pdf(document_id: int):
    database_url = current_app.config["DATABASE_URL"]
    document = get_document(database_url, document_id)

    if not document:
        abort(404)

    allow_pdf = False

    if document["status"] == "approved":
        allow_pdf = True

    if document.get("allow_pdf_export"):
        allow_pdf = True

    if not allow_pdf:
        flash("此公文尚未完成簽核，且不屬於可提前列印流程，暫不可匯出 PDF", "danger")
        return redirect(url_for("approvals.detail", document_id=document_id))

    steps = get_document_steps(database_url, document_id)
    pdf_file = build_approval_pdf(document, steps)

    filename = f"{document['doc_no']}.pdf"
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )

@approvals_bp.route("/<int:document_id>/submit", methods=["POST"])
@login_required
@permission_required("edit_approvals")
def submit(document_id: int):
    database_url = current_app.config["DATABASE_URL"]
    document = get_document(database_url, document_id)

    if not document:
        abort(404)

    if document["applicant_user_id"] != int(current_user.id):
        flash("只能送出自己建立的公文", "danger")
        return redirect(url_for("approvals.detail", document_id=document_id))

    ok, message = submit_document(database_url, document_id)
    flash(message, "success" if ok else "danger")
    return redirect(url_for("approvals.detail", document_id=document_id))


@approvals_bp.route("/my-pending")
@login_required
@permission_required("approve_documents")
def my_pending():
    database_url = current_app.config["DATABASE_URL"]
    documents = list_my_pending_documents(database_url, int(current_user.id))
    return render_template("approvals/my_pending.html", documents=documents)


@approvals_bp.route("/<int:document_id>/action", methods=["POST"])
@login_required
@permission_required("approve_documents")
def action(document_id: int):
    database_url = current_app.config["DATABASE_URL"]

    action = (request.form.get("action") or "").strip()
    note = (request.form.get("note") or "").strip()

    if action not in ["approved", "rejected"]:
        flash("不合法的簽核動作", "danger")
        return redirect(url_for("approvals.detail", document_id=document_id))

    ok, message = approve_document(
        database_url,
        document_id=document_id,
        approver_user_id=int(current_user.id),
        action=action,
        note=note,
    )

    flash(message, "success" if ok else "danger")
    return redirect(url_for("approvals.detail", document_id=document_id))