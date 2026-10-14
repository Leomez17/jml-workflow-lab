"""Process the HR event feed, write the results, and score them against the expected outcome.

Usage:  python -m jml.run
"""
import csv
from pathlib import Path

from jml.directory import Directory
from jml.engine import run
from jml.roles import load_roles

RUN_DATE = "2026-10-12"
ROOT = Path(__file__).resolve().parent.parent
DATA, OUTPUT = ROOT / "data", ROOT / "output"
COMPARE = ["enabled", "account_type", "expires", "department", "job_title", "entitlements"]


def read_csv(path: Path) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list, fields: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    directory = Directory.load(DATA / "directory_before.csv")
    roles = load_roles(DATA / "roles.csv")
    events = read_csv(DATA / "hr_events.csv")
    result = run(directory, roles, events, RUN_DATE)

    OUTPUT.mkdir(exist_ok=True)
    directory.save(OUTPUT / "directory_after.csv")
    write_csv(OUTPUT / "audit_log.csv", directory.audit, ["event_id", "action", "account", "detail"])
    write_csv(OUTPUT / "exceptions.csv", result["exceptions"],
              ["event_id", "effective_date", "event_type", "emp_id", "first_name", "last_name", "reason"])

    print(f"Run date {RUN_DATE}: {len(events)} HR events\n")
    print("Audit log")
    for a in directory.audit:
        print(f"  {a['event_id']}  {a['action']:10} {a['account']:16} {a['detail']}")
    print("\nExceptions (need a person to review)")
    for e in result["exceptions"]:
        print(f"  {e['event_id']}  {e['event_type']:7} {e['emp_id']}  {e['reason']}")
    print("\nScheduled for later")
    for e in result["scheduled"]:
        print(f"  {e['event_id']}  {e['event_type']:7} {e['emp_id']}  effective {e['effective_date']}")
    if result["not_built"]:
        print("\nNot built yet")
        for e in result["not_built"]:
            print(f"  {e['event_id']}  {e['event_type']:7} {e['emp_id']}  handler still a TODO")

    # --- Score ---------------------------------------------------------------
    actual = {r["account"]: r for r in read_csv(OUTPUT / "directory_after.csv")}
    expected = {r["account"]: r for r in read_csv(DATA / "expected_after.csv")}
    correct = [a for a in expected if a in actual and all(actual[a][c] == expected[a][c] for c in COMPARE)]
    wrong = [a for a in expected if a not in correct]
    extra = [a for a in actual if a not in expected]

    want_exc = {r["event_id"] for r in read_csv(DATA / "expected_exceptions.csv")}
    got_exc = {e["event_id"] for e in result["exceptions"]}

    print("\nScore")
    print(f"  Accounts correct:      {len(correct)}/{len(expected)}")
    print(f"  Exceptions raised:     {len(want_exc & got_exc)}/{len(want_exc)}")
    print(f"  Unexpected exceptions: {', '.join(sorted(got_exc - want_exc)) or 'none'}")
    print(f"  Accounts to fix:       {', '.join(wrong) or 'none'}")
    print(f"  Unexpected accounts:   {', '.join(extra) or 'none'}")
    if not wrong and not extra and want_exc == got_exc:
        print("\n  All JML events handled correctly - well done")
    print(f"\nWrote {OUTPUT / 'directory_after.csv'}, audit_log.csv and exceptions.csv")


if __name__ == "__main__":
    main()
