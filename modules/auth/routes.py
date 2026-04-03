from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from database import get_user_by_username, get_user_by_id, get_user_roles, get_user_permissions
from extensions import login_manager
from modules.auth.user import User

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id: str):
    database_url = current_app.config["DATABASE_URL"]
    row = get_user_by_id(database_url, int(user_id))

    if not row:
        return None

    roles = get_user_roles(database_url, row["id"])
    permissions = get_user_permissions(database_url, row["id"])

    return User(
        user_id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        is_active=row["is_active"],
        roles=roles,
        permissions=permissions,
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        database_url = current_app.config["DATABASE_URL"]

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        row = get_user_by_username(database_url, username)

        if not row:
            flash("帳號不存在", "danger")
            return redirect(url_for("auth.login"))

        if not row["is_active"]:
            flash("此帳號已停用", "danger")
            return redirect(url_for("auth.login"))

        if not check_password_hash(row["password_hash"], password):
            flash("密碼錯誤", "danger")
            return redirect(url_for("auth.login"))

        roles = get_user_roles(database_url, row["id"])
        permissions = get_user_permissions(database_url, row["id"])

        user = User(
            user_id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            is_active=row["is_active"],
            roles=roles,
            permissions=permissions,
        )

        login_user(user)
        flash("登入成功", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已登出", "success")
    return redirect(url_for("auth.login"))