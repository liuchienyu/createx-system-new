from flask import Flask, render_template

from config import Config
from database import init_db
from extensions import login_manager
from modules.auth.routes import auth_bp
from modules.dashboard import dashboard_bp
from modules.admin import admin_bp
from modules.finance import finance_bp
from modules.projects import projects_bp
from modules.hr import (
    hr_employees_bp,
    hr_departments_bp,
    hr_job_titles_bp,
    hr_movements_bp,
    hr_leave_bp,
    hr_attendance_bp,
)
from modules.approvals import approvals_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)

    with app.app_context():
        init_db(app.config["DATABASE_URL"])

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(hr_employees_bp)
    app.register_blueprint(hr_departments_bp)
    app.register_blueprint(hr_job_titles_bp)
    app.register_blueprint(hr_movements_bp)
    app.register_blueprint(hr_leave_bp)
    app.register_blueprint(hr_attendance_bp)
    app.register_blueprint(approvals_bp)
    

    @app.errorhandler(403)
    def handle_403(_error):
        return render_template("403.html"), 403

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app