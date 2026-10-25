-- MediSlot database schema

DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name     TEXT    NOT NULL,
  mobile        TEXT    NOT NULL UNIQUE,
  email         TEXT    NOT NULL UNIQUE,
  password_hash TEXT    NOT NULL,
  role          TEXT    NOT NULL DEFAULT 'patient'
                CHECK (role IN ('patient', 'receptionist', 'doctor', 'admin')),
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
