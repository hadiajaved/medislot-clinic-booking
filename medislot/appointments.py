"""Appointment booking with token numbers (Epic MSLOT-7: Appointment Booking and Management)."""
import sqlite3

from .db import get_db
from .scheduling import generate_slots


class SlotUnavailable(Exception):
    """Raised when the requested slot is not offered or is already taken."""


def booked_starts(doctor_id, on_date):
    """Start times of the doctor's active appointments on a date."""
    rows = get_db().execute(
        "SELECT start_time FROM appointments WHERE doctor_id = ? AND appointment_date = ?"
        " AND status != 'cancelled'",
        (doctor_id, on_date),
    ).fetchall()
    return {row["start_time"] for row in rows}


def next_token(doctor_id, on_date):
    """Token numbers run 1, 2, 3... per doctor per day in booking order."""
    row = get_db().execute(
        "SELECT COALESCE(MAX(token_no), 0) + 1 AS next FROM appointments"
        " WHERE doctor_id = ? AND appointment_date = ?",
        (doctor_id, on_date),
    ).fetchone()
    return row["next"]


def book_appointment(doctor_id, patient_id, on_date, start_time, booked_by=None):
    """Book one generated slot for a patient and return the new appointment row.

    The slot must be one that generate_slots() offers for that date, and it must
    not already be held by another active appointment (double booking).
    """
    offered = {slot["start"]: slot["end"] for slot in generate_slots(doctor_id, on_date)}
    if start_time not in offered:
        raise SlotUnavailable("That time is not an available slot for this doctor.")
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO appointments (doctor_id, patient_id, booked_by, appointment_date,"
            " start_time, end_time, token_no) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                doctor_id,
                patient_id,
                booked_by or patient_id,
                on_date,
                start_time,
                offered[start_time],
                next_token(doctor_id, on_date),
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise SlotUnavailable("Sorry, that slot has just been booked by someone else.")
    return get_appointment(cursor.lastrowid)


def list_patient_appointments(patient_id):
    """All appointments of a patient, soonest first."""
    return (
        get_db()
        .execute(
            "SELECT a.*, d.full_name AS doctor_name, d.specialization"
            " FROM appointments a JOIN doctors d ON d.id = a.doctor_id"
            " WHERE a.patient_id = ? ORDER BY a.appointment_date, a.start_time",
            (patient_id,),
        )
        .fetchall()
    )


class NotAllowed(Exception):
    """Raised when a user tries to change an appointment that is not theirs."""


def cancel_appointment(appointment_id, user):
    """Cancel a booked appointment; this frees the slot for other patients."""
    appt = get_appointment(appointment_id)
    if appt is None:
        return None
    if user["role"] not in ("admin", "receptionist") and appt["patient_id"] != user["id"]:
        raise NotAllowed("You can only cancel your own appointments.")
    if appt["status"] != "booked":
        raise SlotUnavailable("Only booked appointments can be cancelled.")
    db = get_db()
    db.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,))
    db.commit()
    return get_appointment(appointment_id)


def get_appointment(appointment_id):
    return (
        get_db()
        .execute(
            "SELECT a.*, d.full_name AS doctor_name, d.specialization, d.consultation_fee,"
            " p.full_name AS patient_name"
            " FROM appointments a JOIN doctors d ON d.id = a.doctor_id"
            " JOIN users p ON p.id = a.patient_id WHERE a.id = ?",
            (appointment_id,),
        )
        .fetchone()
    )


# --- Routes -----------------------------------------------------------------
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for  # noqa: E402

from .auth import login_required  # noqa: E402

bp = Blueprint("appointments", __name__, url_prefix="/appointments")


@bp.route("/book", methods=("POST",))
@login_required
def book():
    doctor_id = request.form.get("doctor_id", type=int)
    on_date = request.form.get("date", "")
    start_time = request.form.get("start_time", "")
    try:
        appt = book_appointment(doctor_id, g.user["id"], on_date, start_time)
    except (SlotUnavailable, ValueError) as exc:
        flash(str(exc) if isinstance(exc, SlotUnavailable) else "Enter the date as YYYY-MM-DD.")
        return redirect(url_for("schedule.slots", doctor_id=doctor_id, date=on_date))
    flash("Appointment booked. Your token number is %d." % appt["token_no"])
    return redirect(url_for("appointments.confirmation", appointment_id=appt["id"]))


@bp.route("/mine")
@login_required
def mine():
    return render_template(
        "appointments/mine.html", appointments=list_patient_appointments(g.user["id"])
    )


@bp.route("/<int:appointment_id>/cancel", methods=("POST",))
@login_required
def cancel(appointment_id):
    try:
        appt = cancel_appointment(appointment_id, g.user)
    except NotAllowed:
        abort(403)
    except SlotUnavailable as exc:
        flash(str(exc))
        return redirect(url_for("appointments.mine"))
    if appt is None:
        abort(404)
    flash("Appointment #%d has been cancelled." % appt["id"])
    return redirect(url_for("appointments.mine"))


@bp.route("/<int:appointment_id>")
@login_required
def confirmation(appointment_id):
    appt = get_appointment(appointment_id)
    if appt is None:
        abort(404)
    if g.user["role"] not in ("admin", "receptionist") and appt["patient_id"] != g.user["id"]:
        abort(403)
    return render_template("appointments/confirmation.html", appt=appt)
