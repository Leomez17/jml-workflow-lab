"""The JML workflow: one handler per HR event type.

handle_joiner is written for you as a worked example. The three exercises are
make_username, handle_leaver and handle_mover. Each exercise's tests skip
until you write it.
"""
from jml.directory import Account, Directory, JMLException
from jml.roles import entitlements_for


def find_account(directory: Directory, emp_id: str) -> Account:
    """Find a person's account by employee ID: never by name, because names repeat."""
    matches = directory.by_emp_id(emp_id)
    if not matches:
        raise JMLException(f"No account found for employee {emp_id}")
    return matches[0]


# --- Worked example ---------------------------------------------------------

def handle_joiner(directory: Directory, roles: dict, ev: dict) -> None:
    """New starter: create one account and grant exactly what their role allows."""
    if directory.by_emp_id(ev["emp_id"]):
        raise JMLException(f"{ev['emp_id']} already has an account: duplicate joiner event")

    target = entitlements_for(roles, ev["department"], ev["job_title"])
    if target is None:
        raise JMLException(f"No role defined for {ev['department']} / {ev['job_title']}")

    try:
        username = make_username(directory, ev["first_name"], ev["last_name"], ev["employment_type"])
    except NotImplementedError:
        username = f"{ev['first_name']}.{ev['last_name']}".lower()   # fallback until exercise 1 is done

    contractor = ev["employment_type"] == "Contractor"
    acc = Account(
        account=username,
        emp_id=ev["emp_id"],
        name=f"{ev['first_name']} {ev['last_name']}",
        department=ev["department"],
        job_title=ev["job_title"],
        account_type="guest" if contractor else "user",
        expires=ev["end_date"] if contractor else "",
    )
    directory.create(acc, ev["event_id"])
    for entitlement in sorted(target):
        directory.grant(acc, entitlement, ev["event_id"])


# --- Exercise 1 -------------------------------------------------------------

def make_username(directory: Directory, first: str, last: str, employment_type: str) -> str:
    """Build a unique username: first.last, lower case.

    - Contractors get ".ext" on the end: ryan.patel.ext
    - If the name is taken, add 2, then 3, and so on: priya.shah2

    Hint: directory.exists(username) tells you if a name is taken. A while
    loop keeps trying the next number until it finds a free one.
    """
    raise NotImplementedError("TODO: exercise 1")


# --- Exercise 2 -------------------------------------------------------------

def handle_leaver(directory: Directory, roles: dict, ev: dict) -> None:
    """Leaver: remove every entitlement, then disable the account.

    Hint: find the account with find_account (it raises JMLException if there
    is none), loop over sorted(acc.entitlements) calling directory.revoke, then
    call directory.disable. Use ev["event_id"] for the audit log.
    """
    raise NotImplementedError("TODO: exercise 2")


# --- Exercise 3 -------------------------------------------------------------

def handle_mover(directory: Directory, roles: dict, ev: dict) -> None:
    """Mover: remove what the old role gave, add what the new role needs, keep the rest.

    Hint: target = entitlements_for(...) for the NEW department and job title.
    If it is None, raise JMLException BEFORE changing anything. Then use set
    maths: current - target are to revoke, target - current are to grant.
    Finish with directory.update_job.
    """
    raise NotImplementedError("TODO: exercise 3")


# --- The workflow -----------------------------------------------------------

HANDLERS = {"joiner": handle_joiner, "mover": handle_mover, "leaver": handle_leaver}


def run(directory: Directory, roles: dict, events: list, run_date: str) -> dict:
    """Process events in date order, up to and including run_date."""
    result = {"exceptions": [], "scheduled": [], "not_built": []}
    for ev in sorted(events, key=lambda e: (e["effective_date"], e["event_id"])):
        if ev["effective_date"] > run_date:
            result["scheduled"].append(ev)
            continue
        try:
            HANDLERS[ev["event_type"]](directory, roles, ev)
        except JMLException as exc:
            result["exceptions"].append({**ev, "reason": str(exc)})
        except NotImplementedError:
            result["not_built"].append(ev)
    return result
