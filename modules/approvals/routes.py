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
)

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

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        doc_type = (request.form.get("doc_type") or "").strip()
        content = (request.form.get("content") or "").strip()

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

        approver_users = list_approver_users(database_url)
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

    approver_users = list_approver_users(database_url)
    return render_template(
        "approvals/create.html",
        suggested_doc_no=generate_doc_no(database_url),
        approver_users=approver_users,
    )


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