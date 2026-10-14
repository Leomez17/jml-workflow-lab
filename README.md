# JML Workflow Lab

A Python simulation of a Joiner-Mover-Leaver (JML) identity lifecycle. A feed of HR events drives account changes: joiners get an account and role-based access, movers swap old access for new, and leavers are disabled with all access removed. Every change is written to an audit log, and events the workflow cannot safely process are sent to an exceptions queue for a person to review.

The sample data continues the fictional Fenwick Valley Health Services from the [Access Review Automation](https://github.com/Leomez17/access-review-automation) project. That project found risky access after the fact; this one stops it being created.

## Run it

```bash
python -m pip install -r requirements.txt
python -m pytest
python -m jml.run
```

`python -m jml.run` processes `data/hr_events.csv` up to the run date, prints the audit log, exceptions and scheduled events, and scores the result against `data/expected_after.csv`.

## Controls demonstrated

| Control | How |
| --- | --- |
| Role-based access | Entitlements come from `data/roles.csv`, never granted ad hoc |
| Birthright access | `* / *` roles go to everyone (Microsoft 365) |
| Least privilege for movers | Old-role access is removed, not added to |
| Timely leaver removal | All entitlements revoked and the account disabled |
| Identity matching | People are matched on employee ID, never on name |
| Unique usernames | Clashes get a number; contractors get `.ext` |
| Contractor expiry | Guest accounts carry their contract end date |
| Fail safe | Unknown employees, duplicate joiners and undefined roles go to the exceptions queue, with no partial changes |
| Effective dating | Future-dated events are scheduled, not applied early |
| Audit trail | Every CREATE, GRANT, REVOKE, DISABLE and UPDATE_JOB is logged |

## Project layout

| Path | Purpose |
| --- | --- |
| `data/directory_before.csv` | The identity store before the run |
| `data/hr_events.csv` | 12 HR events: joiners, movers and leavers |
| `data/roles.csv` | The role catalogue |
| `data/expected_after.csv`, `data/expected_exceptions.csv` | The correct outcome, used for scoring |
| `jml/directory.py` | Accounts, entitlements and the audit log |
| `jml/roles.py` | Loads the role catalogue |
| `jml/engine.py` | One handler per event type, and the workflow loop |
| `jml/run.py` | Runs the workflow, writes the output and scores it |
| `tests/test_jml.py` | Tests for each handler |

## Framework mapping

- ISO/IEC 27001:2022 A.5.16 Identity management, A.5.18 Access rights, A.8.2 Privileged access rights
- NCSC Cyber Assessment Framework, principle B2 Identity and access control
- NHS Data Security and Protection Toolkit, user access management

## Next steps

- Grace periods for movers, so a handover week keeps old access with an expiry date
- Automatic disabling of contractor accounts on their expiry date
- The same workflow in Microsoft Entra ID Lifecycle Workflows
