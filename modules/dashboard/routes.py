from flask import Blueprint, render_template
from flask_login import login_required, current_user

from decorators import permission_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
@permission_required("view_dashboard")
def home():
    return render_template("home.html", user=current_user)


@dashboard_bp.route("/dashboard")
@login_required
@permission_required("view_dashboard")
def index():
    return render_template("home.html", user=current_user)


@dashboard_bp.route("/forbidden")
def forbidden():
    return render_template("403.html"), 403