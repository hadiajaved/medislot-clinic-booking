"""Tests for MSLOT-18: view, reschedule or cancel appointments."""
import pytest

from medislot.appointments import book_appointment, get_appointment
from medislot.scheduling import set_availability

MONDAY = "2026-11-02"


@pytest.fixture
def doctor_with_hours(app, add_doctor):
    doctor_id = add_doctor()
    with app.app_context():
        set_availability(doctor_id, 0, "09:00", "10:00", 15)
    return doctor_id


def test_my_appointments_lists_only_own_bookings(app, client, login, doctor_with_hours):
    login()  # patient 1
    with app.app_context():
        book_appointment(doctor_with_hours, 1, MONDAY, "09:00")
    client.get("/auth/logout")
    login(email="other@example.com", mobile="03111111111")  # patient 2
    with app.app_context():
        book_appointment(doctor_with_hours, 2, MONDAY, "09:15")
    page = client.get("/appointments/mine")
    assert b"09:15" in page.data
    assert b"09:00 - 09:15" not in page.data


def test_my_appointments_empty_state(client, login):
    login()
    page = client.get("/appointments/mine")
    assert b"You have no appointments yet." in page.data


def test_cancel_frees_the_slot_for_rebooking(app, client, login, doctor_with_hours):
    login()
    with app.app_context():
        appt = book_appointment(doctor_with_hours, 1, MONDAY, "09:00")
    response = client.post(f"/appointments/{appt['id']}/cancel", follow_redirects=True)
    assert b"has been cancelled" in response.data
    with app.app_context():
        assert get_appointment(appt["id"])["status"] == "cancelled"
        again = book_appointment(doctor_with_hours, 1, MONDAY, "09:00")  # slot is free again
        assert again["id"] != appt["id"]


def test_cannot_cancel_someone_elses_appointment(app, client, login, doctor_with_hours):
    login()
    with app.app_context():
        appt = book_appointment(doctor_with_hours, 1, MONDAY, "09:00")
    client.get("/auth/logout")
    login(email="other@example.com", mobile="03111111111")
    assert client.post(f"/appointments/{appt['id']}/cancel").status_code == 403
