import os
import tempfile

import pytest

from medislot import create_app
from medislot.db import get_db, init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "test"})
    with app.app_context():
        init_db()
    yield app
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def register(client):
    def _register(
        full_name="Ayesha Khan",
        mobile="03001234567",
        email="ayesha@example.com",
        password="secret123",
    ):
        return client.post(
            "/auth/register",
            data={"full_name": full_name, "mobile": mobile, "email": email, "password": password},
        )

    return _register


@pytest.fixture
def login(client, register):
    """Register (if needed) and log in a user; returns the login response."""

    def _login(email="ayesha@example.com", password="secret123", role="patient", **kwargs):
        register(email=email, password=password, **kwargs)
        if role != "patient":
            with client.application.app_context():
                db = get_db()
                db.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
                db.commit()
        return client.post("/auth/login", data={"email": email, "password": password})

    return _login


@pytest.fixture
def add_doctor(app):
    """Insert a doctor directly and return its id."""
    from medislot.doctors import create_doctor

    def _add(full_name="Dr. Sara Ahmed", specialization="Cardiologist", qualification="MBBS, FCPS", fee=2000):
        with app.app_context():
            return create_doctor(full_name, specialization, qualification, fee)

    return _add
