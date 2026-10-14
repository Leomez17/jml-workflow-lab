"""The identity store: accounts, their entitlements, and an audit log of every change."""
import csv
from dataclasses import dataclass, field
from pathlib import Path


class JMLException(Exception):
    """An HR event the workflow refused to process. A person needs to look at it."""


@dataclass
class Account:
    account: str
    emp_id: str
    name: str
    department: str
    job_title: str
    account_type: str            # "user" for employees, "guest" for contractors
    enabled: bool = True
    expires: str = ""            # yyyy-mm-dd, contractors only
    entitlements: set = field(default_factory=set)   # {"System|Entitlement", ...}


class Directory:
    """Every change goes through these methods, so every change is written to the audit log."""

    def __init__(self):
        self.accounts = {}
        self.audit = []

    # --- Lookups ---------------------------------------------------------

    def exists(self, account: str) -> bool:
        return account in self.accounts

    def by_emp_id(self, emp_id: str) -> list:
        return [a for a in self.accounts.values() if a.emp_id == emp_id]

    # --- Changes (each one is audited) -----------------------------------

    def create(self, acc: Account, event_id: str) -> None:
        if self.exists(acc.account):
            raise JMLException(f"Account name {acc.account} is already taken")
        self.accounts[acc.account] = acc
        self._log(event_id, "CREATE", acc.account, f"{acc.account_type} for {acc.name} ({acc.emp_id})")

    def grant(self, acc: Account, entitlement: str, event_id: str) -> None:
        acc.entitlements.add(entitlement)
        self._log(event_id, "GRANT", acc.account, entitlement)

    def revoke(self, acc: Account, entitlement: str, event_id: str) -> None:
        acc.entitlements.discard(entitlement)
        self._log(event_id, "REVOKE", acc.account, entitlement)

    def disable(self, acc: Account, event_id: str) -> None:
        acc.enabled = False
        self._log(event_id, "DISABLE", acc.account, "account disabled")

    def update_job(self, acc: Account, department: str, job_title: str, event_id: str) -> None:
        old = f"{acc.department} / {acc.job_title}"
        acc.department, acc.job_title = department, job_title
        self._log(event_id, "UPDATE_JOB", acc.account, f"{old} -> {department} / {job_title}")

    def _log(self, event_id, action, account, detail):
        self.audit.append({"event_id": event_id, "action": action, "account": account, "detail": detail})

    # --- Load and save ---------------------------------------------------

    FIELDS = ["account", "emp_id", "name", "department", "job_title",
              "account_type", "enabled", "expires", "entitlements"]

    @classmethod
    def load(cls, path: Path) -> "Directory":
        d = cls()
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ents = set(row["entitlements"].split(";")) if row["entitlements"] else set()
                d.accounts[row["account"]] = Account(
                    row["account"], row["emp_id"], row["name"], row["department"],
                    row["job_title"], row["account_type"], row["enabled"] == "yes",
                    row["expires"], ents,
                )
        return d

    def save(self, path: Path) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.FIELDS)
            w.writeheader()
            for a in sorted(self.accounts.values(), key=lambda a: a.account):
                w.writerow({
                    "account": a.account, "emp_id": a.emp_id, "name": a.name,
                    "department": a.department, "job_title": a.job_title,
                    "account_type": a.account_type, "enabled": "yes" if a.enabled else "no",
                    "expires": a.expires, "entitlements": ";".join(sorted(a.entitlements)),
                })
