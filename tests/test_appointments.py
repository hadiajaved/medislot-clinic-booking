"""Tests for MSLOT-17: book an available appointment slot."""
import pytest

from medislot.appointments import SlotUnavailable, book_appointment, get_appointment
from medislot.scheduling import set_availability

MONDAY = "2026-11-02"


@pytest.fixture
def doctor_with_hours(app, add_doctor):
    doctor_id = add_doctor()
    with app.app_context():
        set_availability(doctor_id, 0, "09:00", "10:00", 15)  # Monday: 09:00 09:15 09:30 09:45
    return doctor_id


def test_booking_assigns_sequential_token_numbers(app, client, login, doctor_with_hours):
    login()  # patient id 1
    with app.app_context():
        first = book_appointment(doctor_with_hours, 1, MONDAY, "09:00")
        second = book_appointment(doctor_with_hours, 1, MONDAY, "09:30")
        assert (first["token_no"], second["token_no"]) == (1, 2)
        assert first["end_time"] == "09:15"
        assert first["status"] == "booked"


def test_double_booking_of_same_slot_is_rejected(app, login, doctor_with_hours):
    login()
    with app.app_context():
        book_appointment(doctor_with_hours, 1, MONDAY, "09:00")
        with pytest.raises(SlotUnavailable):
            book_appointment(doctor_with_hours, 1, MONDAY, "09:00")


def test_cannot_book_time_outside_generated_slots(app, login, doctor_with_hours):
    login()
    with app.app_context():
        with pytest.raises(SlotUnavailable):
            book_appointment(doctor_with_hours, 1, MONDAY, "11:00")  # after working hours
        with pytest.raises(SlotUnavailable):
            book_appointment(doctor_with_hours, 1, "2026-11-03", "09:00")  # Tuesday: no hours


def test_guest_is_redirected_to_login_when_booking(client, doctor_with_hours):
    response = client.post(
        "/appointments/book",
        data={"doctor_id": doctor_with_hours, "date": MONDAY, "start_time": "09:00"},
    )
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_patient_books_through_slot_page_and_sees_confirmation(app, client, login, doctor_with_hours):
    login()
    response = client.post(
        "/appointments/book",
        data={"doctor_id": doctor_with_hours, "date": MONDAY, "start_time": "09:15"},
        follow_redirects=True,
    )
    assert b"Appointment confirmed" in response.data
    assert b"Your token number is 1." in response.data
    assert b"Dr. Sara Ahmed" in response.data
    slots_page = client.get(f"/doctors/{doctor_with_hours}/slots?date={MONDAY}")
    assert slots_page.data.count(b"Book this slot") == 3
    assert b"Booked" in slots_page.data
    with app.app_context():
        assert get_appointment(1)["patient_id"] == 1


def test_other_patient_cannot_view_confirmation(client, login, doctor_with_hours):
    login()
    client.post(
        "/appointments/book",
        data={"doctor_id": doctor_with_hours, "date": MONDAY, "start_time": "09:00"},
    )
    client.get("/auth/logout")
    login(email="someone@example.com", mobile="03111111111")
    assert client.get("/appointments/1").status_code == 403
