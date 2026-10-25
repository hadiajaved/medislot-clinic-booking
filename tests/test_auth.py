"""Tests for MSLOT-10 (patient registration) and MSLOT-11 (secure login and logout)."""
from flask import g, session

from medislot.db import get_db


def test_register_creates_patient_account(app, client, register):
    response = register()
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
    with app.app_context():
        user = get_db().execute("SELECT * FROM users WHERE email = 'ayesha@example.com'").fetchone()
        assert user is not None
        assert user["role"] == "patient"
        assert user["password_hash"] != "secret123"


def test_register_rejects_invalid_mobile_and_short_password(client, register):
    response = client.post(
        "/auth/register",
        data={"full_name": "A", "mobile": "0300123", "email": "a@example.com", "password": "123"},
        follow_redirects=True,
    )
    assert b"Mobile number must be exactly 11 digits." in response.data
    assert b"Password must be at least 8 characters." in response.data


def test_register_rejects_duplicate_email(client, register):
    register()
    response = client.post(
        "/auth/register",
        data={
            "full_name": "Other",
            "mobile": "03009999999",
            "email": "ayesha@example.com",
            "password": "secret123",
        },
        follow_redirects=True,
    )
    assert b"already exists" in response.data


def test_login_and_logout(client, login):
    response = login()
    assert response.status_code == 302
    with client:
        client.get("/")
        assert session["user_id"] == 1
        assert g.user["email"] == "ayesha@example.com"
    response = client.get("/auth/logout", follow_redirects=True)
    with client:
        client.get("/")
        assert "user_id" not in session


def test_login_rejects_wrong_password(client, register):
    register()
    response = client.post(
        "/auth/login", data={"email": "ayesha@example.com", "password": "wrong"}, follow_redirects=True
    )
    assert b"Incorrect email or password." in response.data


def test_login_ignores_external_redirect_target(client, register):
    register()
    response = client.post(
        "/auth/login?next=https://evil.example.com",
        data={"email": "ayesha@example.com", "password": "secret123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
