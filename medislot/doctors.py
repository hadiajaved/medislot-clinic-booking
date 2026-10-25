"""Doctor profile management (Epic MSLOT-6: Doctor and Schedule Management)."""
from .db import get_db

SPECIALIZATIONS = (
    "General Physician",
    "Cardiologist",
    "Dermatologist",
    "ENT Specialist",
    "Gynecologist",
    "Orthopedic Surgeon",
    "Pediatrician",
    "Psychiatrist",
)


def validate_doctor(full_name, specialization, qualification, consultation_fee):
    """Return a list of validation errors for a doctor profile form."""
    errors = []
    if not full_name or not full_name.strip():
        errors.append("Doctor name is required.")
    if specialization not in SPECIALIZATIONS:
        errors.append("Choose a valid specialization.")
    if not qualification or not qualification.strip():
        errors.append("Qualification is required.")
    try:
        fee = int(consultation_fee)
        if fee < 0:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Consultation fee must be a whole number of rupees, 0 or more.")
    return errors


def list_doctors(active_only=True):
    sql = "SELECT * FROM doctors"
    if active_only:
        sql += " WHERE is_active = 1"
    return get_db().execute(sql + " ORDER BY full_name").fetchall()


def get_doctor(doctor_id):
    return get_db().execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()


def create_doctor(full_name, specialization, qualification, consultation_fee, bio=""):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO doctors (full_name, specialization, qualification, consultation_fee, bio)"
        " VALUES (?, ?, ?, ?, ?)",
        (full_name.strip(), specialization, qualification.strip(), int(consultation_fee), bio.strip()),
    )
    db.commit()
    return cursor.lastrowid


def update_doctor(doctor_id, full_name, specialization, qualification, consultation_fee, bio="", is_active=True):
    db = get_db()
    db.execute(
        "UPDATE doctors SET full_name = ?, specialization = ?, qualification = ?,"
        " consultation_fee = ?, bio = ?, is_active = ? WHERE id = ?",
        (
            full_name.strip(),
            specialization,
            qualification.strip(),
            int(consultation_fee),
            bio.strip(),
            1 if is_active else 0,
            doctor_id,
        ),
    )
    db.commit()


# --- Routes -----------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for  # noqa: E402

from .auth import role_required  # noqa: E402

bp = Blueprint("doctors", __name__, url_prefix="/doctors")


@bp.route("/")
def index():
    return render_template("doctors/list.html", doctors=list_doctors())


@bp.route("/add", methods=("GET", "POST"))
@role_required("admin")
def add():
    if request.method == "POST":
        f = request.form
        errors = validate_doctor(
            f.get("full_name"), f.get("specialization"), f.get("qualification"), f.get("consultation_fee")
        )
        if not errors:
            create_doctor(
                f["full_name"], f["specialization"], f["qualification"], f["consultation_fee"], f.get("bio", "")
            )
            flash("Doctor profile added.")
            return redirect(url_for("doctors.index"))
        for error in errors:
            flash(error)
    return render_template("doctors/form.html", doctor=None, specializations=SPECIALIZATIONS)


@bp.route("/<int:doctor_id>/edit", methods=("GET", "POST"))
@role_required("admin")
def edit(doctor_id):
    doctor = get_doctor(doctor_id)
    if doctor is None:
        return ("Doctor not found", 404)
    if request.method == "POST":
        f = request.form
        errors = validate_doctor(
            f.get("full_name"), f.get("specialization"), f.get("qualification"), f.get("consultation_fee")
        )
        if not errors:
            update_doctor(
                doctor_id,
                f["full_name"],
                f["specialization"],
                f["qualification"],
                f["consultation_fee"],
                f.get("bio", ""),
                is_active=bool(f.get("is_active")),
            )
            flash("Doctor profile updated.")
            return redirect(url_for("doctors.index"))
        for error in errors:
            flash(error)
    return render_template("doctors/form.html", doctor=doctor, specializations=SPECIALIZATIONS)
