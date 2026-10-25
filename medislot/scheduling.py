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
