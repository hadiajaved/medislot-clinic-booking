"""Tests for MSLOT-16: search doctors by specialization and date."""
from medislot.doctors import search_doctors
from medislot.scheduling import set_availability

MONDAY = "2026-11-02"
TUESDAY = "2026-11-03"


def _seed(app, add_doctor):
    cardio = add_doctor("Dr. Sara Ahmed", "Cardiologist")
    derma = add_doctor("Dr. Bilal Khan", "Dermatologist")
    with app.app_context():
        set_availability(cardio, 0, "09:00", "12:00", 15)  # Monday
        set_availability(derma, 1, "10:00", "13:00", 20)   # Tuesday
    return cardio, derma


def test_search_by_specialization(app, add_doctor):
    _seed(app, add_doctor)
    with app.app_context():
        names = [d["full_name"] for d in search_doctors(specialization="Cardiologist")]
        assert names == ["Dr. Sara Ahmed"]
        assert len(search_doctors()) == 2


def test_search_by_date_returns_only_doctors_working_that_weekday(app, add_doctor):
    _seed(app, add_doctor)
    with app.app_context():
        assert [d["full_name"] for d in search_doctors(on_date=MONDAY)] == ["Dr. Sara Ahmed"]
        assert [d["full_name"] for d in search_doctors(on_date=TUESDAY)] == ["Dr. Bilal Khan"]
        assert search_doctors(specialization="Cardiologist", on_date=TUESDAY) == []


def test_search_page_shows_matching_doctors(app, client, add_doctor):
    _seed(app, add_doctor)
    page = client.get(f"/doctors/search?specialization=Cardiologist&date={MONDAY}")
    assert b"1 doctor(s) found" in page.data
    assert b"Dr. Sara Ahmed" in page.data
    assert b"Dr. Bilal Khan" not in page.data
    assert f"/doctors/1/slots?date={MONDAY}".encode() in page.data


def test_search_page_without_filters_lists_everyone(app, client, add_doctor):
    _seed(app, add_doctor)
    page = client.get("/doctors/search?specialization=&date=")
    assert b"2 doctor(s) found" in page.data
