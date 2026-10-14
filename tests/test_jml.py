"""Tests for the JML workflow.

Each exercise's tests skip on their own until you write that function:
no skip lines to delete.
"""
from pathlib import Path

import pytest

from jml import engine
from jml.directory import Directory, JMLException
from jml.roles import load_roles

DATA = Path(__file__).resolve().parent.parent / "data"
M365 = "Microsoft 365|Mailbox and Teams"


@pytest.fixture
def directory():
    return Directory.load(DATA / "directory_before.csv")   # a fresh copy for every test


@pytest.fixture
def roles():
    return load_roles(DATA / "roles.csv")


def event(event_id, event_type, emp_id, first="", last="", department="",
          job_title="", employment_type="Employee", end_date=""):
    return {"event_id": event_id, "effective_date": "2026-10-10", "event_type": event_type,
            "emp_id": emp_id, "first_name": first, "last_name": last, "department": department,
            "job_title": job_title, "employment_type": employment_type, "end_date": end_date}


def call(fn, *args):
    """Run an exercise function; skip the test if it is still a TODO."""
    try:
        return fn(*args)
    except NotImplementedError:
        pytest.skip(f"{fn.__name__} not written yet")


# --- Worked example: joiner --------------------------------------------------

def test_joiner_gets_role_access_and_birthright(directory, roles):
    engine.handle_joiner(directory, roles, event("T1", "joiner", "E2001", "Amira", "Hassan", "Clinical", "Staff Nurse"))
    acc = engine.find_account(directory, "E2001")
    assert acc.entitlements == {M365, "CareRecord EPR|Staff Nurse", "Entra ID|GRP-Clinical-Users"}
    assert acc.enabled and acc.account_type == "user"


def test_contractor_joiner_is_guest_with_expiry(directory, roles):
    engine.handle_joiner(directory, roles, event("T1", "joiner", "E2002", "Ryan", "Patel", "IT",
                                                 "Service Desk Analyst", "Contractor", "2026-12-31"))
    acc = engine.find_account(directory, "E2002")
    assert acc.account_type == "guest" and acc.expires == "2026-12-31"


def test_duplicate_joiner_is_rejected(directory, roles):
    with pytest.raises(JMLException):
        engine.handle_joiner(directory, roles, event("T1", "joiner", "E1006", "Daniel", "Kim", "Clinical", "Clinical Coder"))


def test_future_dated_event_is_scheduled_not_applied(directory, roles):
    ev = event("T1", "leaver", "E1005")
    ev["effective_date"] = "2026-10-31"
    result = engine.run(directory, roles, [ev], "2026-10-12")
    assert result["scheduled"] == [ev]
    assert directory.accounts["grace.bennett"].enabled


# --- Exercise 1: make_username ----------------------------------------------

def test_username_is_first_dot_last(directory):
    assert call(engine.make_username, directory, "Amira", "Hassan", "Employee") == "amira.hassan"


def test_username_clash_adds_a_number(directory):
    assert call(engine.make_username, directory, "Priya", "Shah", "Employee") == "priya.shah2"


def test_contractor_username_ends_ext(directory):
    assert call(engine.make_username, directory, "Ryan", "Patel", "Contractor") == "ryan.patel.ext"


# --- Exercise 2: handle_leaver ----------------------------------------------

def test_leaver_loses_all_access_and_is_disabled(directory, roles):
    call(engine.handle_leaver, directory, roles, event("T1", "leaver", "E1008"))
    acc = directory.accounts["james.turner"]
    assert acc.entitlements == set()
    assert not acc.enabled


def test_unknown_leaver_raises_exception(directory, roles):
    with pytest.raises(JMLException):
        call(engine.handle_leaver, directory, roles, event("T1", "leaver", "E1999"))


# --- Exercise 3: handle_mover -----------------------------------------------

def test_mover_swaps_old_role_for_new(directory, roles):
    call(engine.handle_mover, directory, roles, event("T1", "mover", "E1006", "Daniel", "Kim", "HR", "HR Advisor"))
    acc = directory.accounts["daniel.kim"]
    assert acc.entitlements == {M365, "HRConnect|HR Advisor", "Entra ID|GRP-HR-Users"}
    assert (acc.department, acc.job_title) == ("HR", "HR Advisor")


def test_mover_to_unknown_role_changes_nothing(directory, roles):
    before = set(directory.accounts["hannah.lewis"].entitlements)
    with pytest.raises(JMLException):
        call(engine.handle_mover, directory, roles, event("T1", "mover", "E1003", "Hannah", "Lewis", "IT", "Cloud Architect"))
    assert directory.accounts["hannah.lewis"].entitlements == before
