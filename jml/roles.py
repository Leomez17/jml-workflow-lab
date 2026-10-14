"""The role catalogue: which entitlements each job gets (role-based access control)."""
import csv
from pathlib import Path

BIRTHRIGHT = ("*", "*")   # rows marked * / * go to everyone


def load_roles(path: Path) -> dict:
    """Return {(department, job_title): {"System|Entitlement", ...}}."""
    roles = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            roles.setdefault((row["department"], row["job_title"]), set()).add(row["entitlement"])
    return roles


def entitlements_for(roles: dict, department: str, job_title: str):
    """Everything a person in this job should have: birthright access plus their role.

    Returns None when the job is not in the catalogue, so the caller can refuse
    to guess.
    """
    role = roles.get((department, job_title))
    if role is None:
        return None
    return roles.get(BIRTHRIGHT, set()) | role
