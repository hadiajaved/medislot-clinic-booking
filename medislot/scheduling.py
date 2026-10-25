"""Weekly doctor availability and bookable slot generation (MSLOT-14)."""
from datetime import date, datetime, timedelta

from .db import get_db

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
SLOT_LENGTHS = (10, 15, 20, 30, 45, 60)


def parse_time(value):
    """Parse 'HH:MM' into a time object (raises ValueError when malformed)."""
    return datetime.strptime(value, "%H:%M").time()


def validate_availability(weekday, start_time, end_time, slot_minutes):
    """Return a list of validation errors for one availability row."""
    errors = []
    try:
        if not 0 <= int(weekday) <= 6:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Choose a valid weekday.")
    try:
        if parse_time(start_time or "") >= parse_time(end_time or ""):
            errors.append("End time must be after start time.")
    except ValueError:
        errors.append("Times must be in HH:MM format.")
    try:
        if int(slot_minutes) not in SLOT_LENGTHS:
            raise ValueError
    except (TypeError, ValueError):
        errors.append(
            "Consultation duration must be one of "
            + ", ".join(str(m) for m in SLOT_LENGTHS)
            + " minutes."
        )
    return errors


def set_availability(doctor_id, weekday, start_time, end_time, slot_minutes):
    """Create or replace the availability of a doctor for one weekday."""
    db = get_db()
    db.execute(
        "INSERT INTO availability (doctor_id, weekday, start_time, end_time, slot_minutes)"
        " VALUES (?, ?, ?, ?, ?)"
        " ON CONFLICT(doctor_id, weekday) DO UPDATE SET"
        " start_time = excluded.start_time, end_time = excluded.end_time,"
        " slot_minutes = excluded.slot_minutes",
        (doctor_id, int(weekday), start_time, end_time, int(slot_minutes)),
    )
    db.commit()


def get_availability(doctor_id):
    return (
        get_db()
        .execute(
            "SELECT * FROM availability WHERE doctor_id = ? ORDER BY weekday", (doctor_id,)
        )
        .fetchall()
    )


def remove_availability(doctor_id, weekday):
    db = get_db()
    db.execute(
        "DELETE FROM availability WHERE doctor_id = ? AND weekday = ?", (doctor_id, int(weekday))
    )
    db.commit()


def slots_between(start_time, end_time, slot_minutes):
    """Pure helper: consecutive (start, end) 'HH:MM' pairs that fit in the window."""
    today = date.today()
    cursor = datetime.combine(today, parse_time(start_time))
    end = datetime.combine(today, parse_time(end_time))
    step = timedelta(minutes=int(slot_minutes))
    slots = []
    while cursor + step <= end:
        slots.append((cursor.strftime("%H:%M"), (cursor + step).strftime("%H:%M")))
        cursor += step
    return slots


def generate_slots(doctor_id, on_date):
    """Return the bookable slots of a doctor on a calendar date.

    ``on_date`` may be a ``date`` or an ISO string. Days without availability
    produce an empty list, so patients are never offered them.
    """
    if isinstance(on_date, str):
        on_date = date.fromisoformat(on_date)
    row = (
        get_db()
        .execute(
            "SELECT * FROM availability WHERE doctor_id = ? AND weekday = ?",
            (doctor_id, on_date.weekday()),
        )
        .fetchone()
    )
    if row is None:
        return []
    return [
        {"date": on_date.isoformat(), "start": start, "end": end}
        for start, end in slots_between(row["start_time"], row["end_time"], row["slot_minutes"])
    ]


# --- Routes -----------------------------------------------------------------
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for  # noqa: E402

from .auth import login_required  # noqa: E402
from .doctors import get_doctor  # noqa: E402

bp = Blueprint("schedule", __name__, url_prefix="/doctors")


def _doctor_for_management(doctor_id):
    """Load the doctor and stop unless the user is an admin or that doctor's own account."""
    doctor = get_doctor(doctor_id)
    if doctor is None:
        abort(404)
    is_admin = g.user["role"] == "admin"
    is_own_profile = g.user["role"] == "doctor" and doctor["user_id"] == g.user["id"]
    if not (is_admin or is_own_profile):
        abort(403)
    return doctor


@bp.route("/<int:doctor_id>/availability", methods=("GET", "POST"))
@login_required
def availability(doctor_id):
    doctor = _doctor_for_management(doctor_id)
    if request.method == "POST":
        f = request.form
        errors = validate_availability(
            f.get("weekday"), f.get("start_time"), f.get("end_time"), f.get("slot_minutes")
        )
        if not errors:
            set_availability(
                doctor_id, f["weekday"], f["start_time"], f["end_time"], f["slot_minutes"]
            )
            flash("Availability saved.")
            return redirect(url_for("schedule.availability", doctor_id=doctor_id))
        for error in errors:
            flash(error)
    return render_template(
        "doctors/availability.html",
        doctor=doctor,
        availability=get_availability(doctor_id),
        weekdays=WEEKDAYS,
        slot_lengths=SLOT_LENGTHS,
    )


@bp.route("/<int:doctor_id>/availability/<int:weekday>/remove", methods=("POST",))
@login_required
def remove_day(doctor_id, weekday):
    _doctor_for_management(doctor_id)
    remove_availability(doctor_id, weekday)
    flash("Availability removed.")
    return redirect(url_for("schedule.availability", doctor_id=doctor_id))


@bp.route("/<int:doctor_id>/slots")
def slots(doctor_id):
    doctor = get_doctor(doctor_id)
    if doctor is None:
        return ("Doctor not found", 404)
    on_date = request.args.get("date", "")
    slot_list = []
    if on_date:
        try:
            slot_list = generate_slots(doctor_id, on_date)
        except ValueError:
            flash("Enter the date as YYYY-MM-DD.")
            on_date = ""
    return render_template("doctors/slots.html", doctor=doctor, on_date=on_date, slots=slot_list)
