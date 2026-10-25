"""Tests for MSLOT-13: add and update doctor profiles."""
from medislot.doctors import get_doctor, list_doctors

DOCTOR = {
    "full_name": "Dr. Sara Ahmed",
    "specialization": "Cardiologist",
    "qualification": "MBBS, FCPS (Cardiology)",
    "consultation_fee": "2000",
    "bio": "15 years of experience.",
}


def test_admin_can_add_doctor(app, client, login):
    login(role="admin")
    response = client.post("/doctors/add", data=DOCTOR, follow_redirects=True)
    assert b"Doctor profile added." in response.data
    assert b"Dr. Sara Ahmed" in response.data
    with app.app_context():
        doctor = list_doctors()[0]
        assert doctor["specialization"] == "Cardiologist"
        assert doctor["consultation_fee"] == 2000


def test_patient_cannot_add_doctor(client, login):
    login(role="patient")
    assert client.post("/doctors/add", data=DOCTOR).status_code == 403


def test_anonymous_is_redirected_to_login(client):
    response = client.get("/doctors/add")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_add_doctor_rejects_negative_fee(client, login):
    login(role="admin")
    response = client.post(
        "/doctors/add", data={**DOCTOR, "consultation_fee": "-5"}, follow_redirects=True
    )
    assert b"Consultation fee must be a whole number" in response.data


def test_admin_can_update_doctor(app, client, login):
    login(role="admin")
    client.post("/doctors/add", data=DOCTOR)
    response = client.post(
        "/doctors/1/edit",
        data={**DOCTOR, "consultation_fee": "2500", "is_active": "1"},
        follow_redirects=True,
    )
    assert b"Doctor profile updated." in response.data
    with app.app_context():
        assert get_doctor(1)["consultation_fee"] == 2500


def test_deactivated_doctor_hidden_from_list(app, client, login):
    login(role="admin")
    client.post("/doctors/add", data=DOCTOR)
    client.post("/doctors/1/edit", data=DOCTOR)  # checkbox missing -> inactive
    with app.app_context():
        assert list_doctors() == []
        assert get_doctor(1)["is_active"] == 0
