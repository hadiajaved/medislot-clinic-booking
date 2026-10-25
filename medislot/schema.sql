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

DROP TABLE IF EXISTS doctors;

CREATE TABLE doctors (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name        TEXT    NOT NULL,
  specialization   TEXT    NOT NULL,
  qualification    TEXT    NOT NULL,
  consultation_fee INTEGER NOT NULL CHECK (consultation_fee >= 0),
  bio              TEXT    NOT NULL DEFAULT '',
  is_active        INTEGER NOT NULL DEFAULT 1,
  user_id          INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- the doctor's own login, if any
  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS availability;

-- One row per doctor per weekday: the working window and the consultation length.
CREATE TABLE availability (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  doctor_id    INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
  weekday      INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),   -- 0 = Monday
  start_time   TEXT    NOT NULL,                                    -- 'HH:MM'
  end_time     TEXT    NOT NULL,
  slot_minutes INTEGER NOT NULL DEFAULT 15,
  UNIQUE (doctor_id, weekday)
);

DROP TABLE IF EXISTS appointments;

CREATE TABLE appointments (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  doctor_id        INTEGER NOT NULL REFERENCES doctors(id),
  patient_id       INTEGER NOT NULL REFERENCES users(id),
  booked_by        INTEGER NOT NULL REFERENCES users(id),   -- patient, or receptionist on their behalf
  appointment_date TEXT    NOT NULL,                        -- 'YYYY-MM-DD'
  start_time       TEXT    NOT NULL,                        -- 'HH:MM'
  end_time         TEXT    NOT NULL,
  token_no         INTEGER NOT NULL,                        -- queue number for that doctor and day
  status           TEXT    NOT NULL DEFAULT 'booked'
                   CHECK (status IN ('booked', 'cancelled', 'completed')),
  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A slot can be held by only one active appointment (cancelled ones free it again).
CREATE UNIQUE INDEX ux_active_slot
  ON appointments (doctor_id, appointment_date, start_time)
  WHERE status != 'cancelled';
