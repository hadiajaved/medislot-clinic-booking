"""MediSlot Clinic Appointment Booking System - Flask application factory."""
import os

from flask import Flask, render_template


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("MEDISLOT_SECRET_KEY", "dev-only-insecure-key"),
        DATABASE=os.path.join(app.instance_path, "medislot.sqlite"),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    from . import db

    db.init_app(app)

    from . import auth

    app.register_blueprint(auth.bp)

    from . import doctors

    app.register_blueprint(doctors.bp)

    from . import scheduling

    app.register_blueprint(scheduling.bp)

    from . import appointments

    app.register_blueprint(appointments.bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
