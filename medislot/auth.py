"""User registration, login and logout (Epic MSLOT-5: User Management and Authentication)."""
import functools
import re

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

MOBILE_RE = re.compile(r"^\d{11}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def safe_next_url(target):
    """Only allow redirects to local paths, never to another site (open redirect)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return url_for("index")


def validate_registration(full_name, mobile, email, password):
    """Return a list of validation errors for the registration form."""
    errors = []
    if not full_name or not full_name.strip():
        errors.append("Full name is required.")
    if not MOBILE_RE.match(mobile or ""):
        errors.append("Mobile number must be exactly 11 digits.")
    if not EMAIL_RE.match(email or ""):
        errors.append("Enter a valid email address.")
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    return errors


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        form = request.form
        errors = validate_registration(
            form.get("full_name"), form.get("mobile"), form.get("email"), form.get("password")
        )
        if not errors:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (full_name, mobile, email, password_hash)"
                    " VALUES (?, ?, ?, ?)",
                    (
                        form["full_name"].strip(),
                        form["mobile"],
                        form["email"].strip().lower(),
                        generate_password_hash(form["password"]),
                    ),
                )
                db.commit()
            except db.IntegrityError:
                errors.append("An account with this mobile number or email already exists.")
            else:
                flash("Registration successful. Please log in.")
                return redirect(url_for("auth.login"))
        for error in errors:
            flash(error)
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(safe_next_url(request.args.get("next")))
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = (
        None
        if user_id is None
        else get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    )


def login_required(view):
    """Redirect anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def role_required(*roles):
    """Allow only logged-in users whose role is in ``roles``."""

    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for("auth.login", next=request.path))
            if g.user["role"] not in roles:
                return ("Forbidden: this action requires role " + " or ".join(roles), 403)
            return view(**kwargs)

        return wrapped_view

    return decorator
