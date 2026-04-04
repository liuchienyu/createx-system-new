from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user

from decorators import permission_required
from modules.dashboard.services import build_dashboard_context

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
@permission_required("view_dashboard")
def home():
    database_url = current_app.config["DATABASE_URL"]
    context = build_dashboard_context(database_url, int(current_user.id))
    return render_template("dashboard/index.html", **context)


@dashboard_bp.route("/dashboard")
@login_required
@permission_required("view_dashboard")
def index():
    database_url = current_app.config["DATABASE_URL"]
    context = build_dashboard_context(database_url, int(current_user.id))
    return render_template("dashboard/index.html", **context)