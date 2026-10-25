"""Tests for MSLOT-14: define weekly availability and generate slots."""
from medislot.scheduling import (
    generate_slots,
    get_availability,
    set_availability,
    slots_between,
    validate_availability,
)

MONDAY = "2026-11-02"
TUESDAY = "2026-11-03"


def test_slots_between_cuts_window_into_consultations():
    assert slots_between("09:00", "10:00", 15) == [
        ("09:00", "09:15"),
        ("09:15", "09:30"),
        ("09:30", "09:45"),
        ("09:45", "10:00"),
    ]
    # a partial slot at the end is never offered
    assert slots_between("09:00", "09:50", 20) == [("09:00", "09:20"), ("09:20", "09:40")]


def test_generate_slots_only_for_working_weekday(app, add_doctor):
    doctor_id = add_doctor()
    with app.app_context():
        set_availability(doctor_id, 0, "09:00", "09:30", 15)  # Monday only
        monday = generate_slots(doctor_id, MONDAY)
        assert [s["start"] for s in monday] == ["09:00", "09:15"]
        assert monday[0]["date"] == MONDAY
        assert generate_slots(doctor_id, TUESDAY) == []


def test_set_availability_replaces_existing_weekday(app, add_doctor):
    doctor_id = add_doctor()
    with app.app_context():
        set_availability(doctor_id, 2, "09:00", "12:00", 15)
        set_availability(doctor_id, 2, "14:00", "16:00", 30)
        rows = get_availability(doctor_id)
        assert len(rows) == 1
        assert (rows[0]["start_time"], rows[0]["slot_minutes"]) == ("14:00", 30)


def test_validate_availability_reports_errors():
    errors = validate_availability("9", "10:00", "09:00", "7")
    assert "Choose a valid weekday." in errors
    assert "End time must be after start time." in errors
    assert any(e.startswith("Consultation duration") for e in errors)
    assert validate_availability("0", "09:00", "10:00", "15") == []


def test_admin_can_save_availability_through_form(app, client, login, add_doctor):
    doctor_id = add_doctor()
    login(role="admin")
    response = client.post(
        f"/doctors/{doctor_id}/availability",
        data={"weekday": "0", "start_time": "09:00", "end_time": "10:00", "slot_minutes": "15"},
        follow_redirects=True,
    )
    assert b"Availability saved." in response.data
    assert b"Monday" in response.data
    page = client.get(f"/doctors/{doctor_id}/slots?date={MONDAY}")
    assert b"09:45" in page.data


def test_patient_cannot_edit_availability(client, login, add_doctor):
    doctor_id = add_doctor()
    login(role="patient")
    assert client.get(f"/doctors/{doctor_id}/availability").status_code == 403
