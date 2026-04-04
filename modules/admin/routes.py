from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user

from decorators import permission_required
from modules.admin.services import (
    list_users,
    get_user,
    create_user,
    update_user,
    update_user_with_password,
    reset_user_password,
    delete_user,
    list_roles,
    get_user_role_ids,
    assign_user_roles,
    owner_count,
    is_owner_user,
)
from modules.admin.role_services import (
    list_roles_with_permission_count,
    get_role,
    get_all_permissions,
    get_role_permission_ids,
    create_role,
    update_role,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@permission_required("admin_users")
def users_index():
    database_url = current_app.config["DATABASE_URL"]
    users = list_users(database_url)
    return render_template("admin/users_index.html", users=users)


@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@permission_required("admin_users")
def user_create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        display_name = (request.form.get("display_name") or "").strip()
        password = request.form.get("password") or ""
        is_active = request.form.get("is_active") == "on"
        selected_role_ids = [int(x) for x in request.form.getlist("role_ids")]

        if not username:
            flash("請輸入帳號", "danger")
            return redirect(url_for("admin.user_create"))

        if not password:
            flash("請輸入密碼", "danger")
            return redirect(url_for("admin.user_create"))

        ok, message, user_id = create_user(
            database_url=database_url,
            username=username,
            display_name=display_name,
            password=password,
            is_active=is_active,
        )
        if not ok:
            flash(message, "danger")
            return redirect(url_for("admin.user_create"))

        assign_user_roles(database_url, user_id, selected_role_ids)

        flash(message, "success")
        return redirect(url_for("admin.users_index"))

    all_roles = list_roles(database_url)
    return render_template("admin/user_create.html", all_roles=all_roles)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("admin_users")
def user_edit(user_id: int):
    database_url = current_app.config["DATABASE_URL"]
    user_row = get_user(database_url, user_id)

    if not user_row:
        abort(404)

    if request.method == "POST":
        display_name = (request.form.get("display_name") or "").strip()
        password = request.form.get("password") or ""
        is_active = request.form.get("is_active") == "on"

        if int(current_user.id) == user_id and not is_active:
            flash("不能停用目前正在登入的帳號", "danger")
            return redirect(url_for("admin.user_edit", user_id=user_id))

        if is_owner_user(database_url, user_id) and owner_count(database_url) <= 1 and not is_active:
            flash("至少需要一個 Owner，無法停用唯一管理員", "danger")
            return redirect(url_for("admin.user_edit", user_id=user_id))

        final_display_name = display_name or user_row["username"]

        if password:
            update_user_with_password(database_url, user_id, final_display_name, password, is_active)
        else:
            update_user(database_url, user_id, final_display_name, is_active)

        flash("使用者資料已更新", "success")
        return redirect(url_for("admin.users_index"))

    return render_template("admin/user_edit.html", target_user=user_row)


@admin_bp.route("/users/<int:user_id>/roles", methods=["GET", "POST"])
@login_required
@permission_required("admin_users")
def user_roles(user_id: int):
    database_url = current_app.config["DATABASE_URL"]
    user_row = get_user(database_url, user_id)

    if not user_row:
        abort(404)

    if request.method == "POST":
        selected_role_ids = [int(x) for x in request.form.getlist("role_ids")]
        assign_user_roles(database_url, user_id, selected_role_ids)
        flash("使用者角色已更新", "success")
        return redirect(url_for("admin.users_index"))

    all_roles = list_roles(database_url)
    current_role_ids = get_user_role_ids(database_url, user_id)

    return render_template(
        "admin/user_roles.html",
        target_user=user_row,
        all_roles=all_roles,
        current_role_ids=current_role_ids,
    )


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["GET", "POST"])
@login_required
@permission_required("admin_users")
def user_reset_password(user_id: int):
    database_url = current_app.config["DATABASE_URL"]
    user_row = get_user(database_url, user_id)

    if not user_row:
        abort(404)

    if request.method == "POST":
        new_password = request.form.get("new_password") or ""

        if not new_password.strip():
            flash("請輸入新密碼", "danger")
            return redirect(url_for("admin.user_reset_password", user_id=user_id))

        reset_user_password(database_url, user_id, new_password)
        flash("密碼已重設成功", "success")
        return redirect(url_for("admin.users_index"))

    return render_template("admin/user_reset_password.html", target_user=user_row)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@permission_required("admin_users")
def user_toggle_active(user_id: int):
    database_url = current_app.config["DATABASE_URL"]
    user_row = get_user(database_url, user_id)

    if not user_row:
        abort(404)

    new_active = not user_row["is_active"]

    if int(current_user.id) == user_id and not new_active:
        flash("不能停用目前正在登入的帳號", "danger")
        return redirect(url_for("admin.users_index"))

    if is_owner_user(database_url, user_id) and owner_count(database_url) <= 1 and not new_active:
        flash("至少需要一個 Owner，無法停用唯一管理員", "danger")
        return redirect(url_for("admin.users_index"))

    update_user(
        database_url=database_url,
        user_id=user_id,
        display_name=user_row["display_name"] or user_row["username"],
        is_active=new_active,
    )

    flash("使用者狀態已更新", "success")
    return redirect(url_for("admin.users_index"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@permission_required("admin_users")
def user_delete(user_id: int):
    database_url = current_app.config["DATABASE_URL"]
    user_row = get_user(database_url, user_id)

    if not user_row:
        abort(404)

    if int(current_user.id) == user_id:
        flash("不能刪除目前正在登入的帳號", "danger")
        return redirect(url_for("admin.users_index"))

    if is_owner_user(database_url, user_id) and owner_count(database_url) <= 1:
        flash("至少需要一個 Owner，無法刪除唯一管理員", "danger")
        return redirect(url_for("admin.users_index"))

    delete_user(database_url, user_id)
    flash("使用者已刪除", "success")
    return redirect(url_for("admin.users_index"))


@admin_bp.route("/roles")
@login_required
@permission_required("admin_roles")
def roles_index():
    database_url = current_app.config["DATABASE_URL"]
    roles = list_roles_with_permission_count(database_url)
    return render_template("admin/roles_index.html", roles=roles)


@admin_bp.route("/roles/create", methods=["GET", "POST"])
@login_required
@permission_required("admin_roles")
def role_create():
    database_url = current_app.config["DATABASE_URL"]

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        permission_ids = [int(x) for x in request.form.getlist("permission_ids")]

        if not name:
            flash("請輸入角色名稱", "danger")
            return redirect(url_for("admin.role_create"))

        ok, message = create_role(database_url, name, description, permission_ids)
        flash(message, "success" if ok else "danger")

        if ok:
            return redirect(url_for("admin.roles_index"))

        return redirect(url_for("admin.role_create"))

    permissions = get_all_permissions(database_url)
    return render_template("admin/role_create.html", permissions=permissions)


@admin_bp.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("admin_roles")
def role_edit(role_id: int):
    database_url = current_app.config["DATABASE_URL"]
    role = get_role(database_url, role_id)

    if not role:
        abort(404)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        permission_ids = [int(x) for x in request.form.getlist("permission_ids")]

        if not name:
            flash("請輸入角色名稱", "danger")
            return redirect(url_for("admin.role_edit", role_id=role_id))

        ok, message = update_role(database_url, role_id, name, description, permission_ids)
        flash(message, "success" if ok else "danger")

        if ok:
            return redirect(url_for("admin.roles_index"))

        return redirect(url_for("admin.role_edit", role_id=role_id))

    permissions = get_all_permissions(database_url)
    current_permission_ids = get_role_permission_ids(database_url, role_id)

    return render_template(
        "admin/role_edit.html",
        role=role,
        permissions=permissions,
        current_permission_ids=current_permission_ids,
    )