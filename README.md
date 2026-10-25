# MediSlot - Clinic Appointment Booking System

| | |
|---|---|
| **Course** | CS4002 Fundamentals of Software Project Management (Section 9C) |
| **Assignment** | Assignment 2 - Jira-GitHub Integrated Development Workflow |
| **Instructor** | Ms. Maham Saleem |
| **University** | FAST-NUCES, Chiniot-Faisalabad Campus |

## Project purpose

MediSlot is a web based appointment booking system for a small clinic. Patients register an
account, search doctors by specialization and date, and book a free time slot that comes with a
token number, so they do not have to wait in a long queue at the clinic. Doctors define their
weekly availability and leave days, receptionists can book on behalf of walk in patients, and the
clinic manager gets daily and weekly reports. The goal of the project is to reduce patient waiting
time and cut no shows through confirmations and reminders.

## Group members

| Name | Student ID | GitHub |
|---|---|---|
| Hadia Javed | 22F-3354 | [@hadiajaved](https://github.com/hadiajaved) |

## Jira project

- Jira Scrum project: <https://medislot-clinic-9c.atlassian.net/browse/MSLOT> (project key `MSLOT`)
- Every branch, commit and pull request in this repository carries a Jira issue key so that the
  work is traceable from the Jira backlog to the code.

## Technologies

- **Python 3.13** with **Flask 3** (web framework, Jinja2 templates)
- **SQLite** through Python's built in `sqlite3` module (database)
- **pytest** (automated tests)
- **Git and GitHub** (version control, branches, pull requests, code review)
- **Jira Software** (Scrum backlog, sprints) and **GitHub for Jira** (integration)

## Project structure

```
medislot-clinic-booking/
├── run.py                 # development entry point
├── requirements.txt
├── medislot/              # Flask application package
│   ├── __init__.py        # application factory (create_app)
│   ├── db.py              # SQLite connection helpers and init-db command
│   ├── schema.sql         # database schema (users, doctors, availability, appointments)
│   ├── auth.py            # registration, login, logout         (MSLOT-10, MSLOT-11)
│   ├── doctors.py         # doctor profiles and doctor search    (MSLOT-13, MSLOT-16)
│   ├── scheduling.py      # weekly availability and slot generation (MSLOT-14)
│   ├── appointments.py    # slot booking with token numbers, my appointments, cancel (MSLOT-17, MSLOT-18)
│   └── templates/         # Jinja2 HTML templates
└── tests/                 # pytest test suite (one file per Jira story)
```

## Sprint 2 - Appointment Booking Flow

| Jira issue | Branch | Pull request |
|---|---|---|
| MSLOT-13 Add and update doctor profiles | `MSLOT-13-doctor-profiles` | #1 |
| MSLOT-14 Define weekly availability and generate slots | `MSLOT-14-weekly-availability-slots`, `MSLOT-14-availability-ownership-check` | #2, #4 |
| MSLOT-16 Search doctors by specialization and date | `MSLOT-16-doctor-search` | #3 |
| MSLOT-17 Book an available appointment slot | `MSLOT-17-book-appointment-slot` | #5 |
| MSLOT-18 View, reschedule or cancel appointments | `MSLOT-18-manage-appointments` | #6 (draft, reschedule pending) |

## Known limitations (future backlog items)

- Forms do not yet carry CSRF tokens; a Flask-WTF based protection is planned.
- Booking does not yet reject dates in the past or hide slots that have already passed today.
- Doctor leave days (MSLOT-15), receptionist booking (MSLOT-19), notifications (MSLOT-20) and the
  manager dashboard (MSLOT-21) are still in the product backlog.

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app medislot init-db       # create the SQLite database
python run.py                      # http://127.0.0.1:5000
pytest                             # run the tests
```

## Branch, commit and pull request conventions

| Item | Format | Example |
|---|---|---|
| Branch | `MSLOT-<n>-short-description` | `MSLOT-17-book-appointment-slot` |
| Commit | `MSLOT-<n> <what changed>` | `MSLOT-17 Add booking route with double booking prevention` |
| Pull request | `MSLOT-<n>: <summary>` | `MSLOT-17: Book an available appointment slot` |

Workflow: create a branch from `main` for one Jira issue, make small commits, open a pull request,
review, merge, and move the Jira issue from To Do to In Progress to Done.
