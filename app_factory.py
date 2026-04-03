from flask import Flask, render_template

from config import Config
from database import init_db
from extensions import login_manager
from modules.auth.routes import auth_bp
from modules.dashboard.routes import dashboard_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)

    with app.app_context():
        init_db(app.config["DATABASE_URL"])

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    @app.errorhandler(403)
    def handle_403(_error):
        return render_template("403.html"), 403

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app