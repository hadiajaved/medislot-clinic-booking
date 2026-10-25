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
