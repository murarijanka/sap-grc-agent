"""The 12 Level 1 checks. Each is a fixed, repeatable rule: AI never decides a finding.

Every finding records the source file and row it came from.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

# Defaults; a customer can change these in config.
SETTINGS = {
    "expiry_window_days": 90,          # check 5
    "evidence_max_age_days": 365,      # check 6
    "max_users_per_ff_id": 5,          # check 7
    "min_reason_length": 15,           # check 8
    "vague_reasons": {"test", "fix", "support", "issue", "urgent", "na", "n/a", "ok", "check", "access"},
    "review_window_days": 7,           # check 9
    "unused_action_days": 365,         # check 2
    "sensitive_actions": {"SE38", "SE16N", "SE11", "SE37", "SA38", "SM30", "SM31", "SU01",
                          "PFCG", "SCC4", "SE06", "STMS", "SM59", "SU10", "SE80"},  # check 11
}


@dataclass
class Finding:
    check_id: int
    area: str
    severity: str          # High / Medium / Low
    record: str            # the object the finding is about
    reason: str            # deterministic explanation
    action: str            # recommended human action
    source: list = field(default_factory=list)   # ["file.csv row 7", ...]


def _d(s):
    """Parse YYYY-MM-DD (or YYYY-MM-DD HH:MM); return None if blank or invalid."""
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _src(*rows):
    return [f"{r['_file']} row {r['_row']}" for r in rows]


def _yes(v):
    return v.strip().upper() in {"Y", "YES", "X", "TRUE", "1", "ACTIVE"}


def _active_users(users):
    if users is None:
        return None
    return {u["user_id"].upper() for u in users if u["status"].strip().lower() == "active"}


# ---------- Rule set ----------

def check_01_risk_functions(d, today, s):
    """Risks with no active functions, or duplicate definitions (same function set)."""
    out, by_risk = [], {}
    for r in d["ruleset"]:
        if _yes(r["risk_active"]):
            by_risk.setdefault(r["risk_id"], []).append(r)
    signatures = {}
    for risk, rows in sorted(by_risk.items()):
        active_fns = {r["function_id"] for r in rows if _yes(r["function_active"])}
        if not active_fns:
            out.append(Finding(1, "Rule set", "High", risk,
                               "Active risk has no active functions, so it can never be detected.",
                               "Deactivate the risk or attach the correct functions.", _src(*rows[:3])))
            continue
        sig = frozenset(active_fns)
        if sig in signatures:
            out.append(Finding(1, "Rule set", "Medium", risk,
                               f"Same active functions as risk {signatures[sig]}: duplicate definition, double-counted violations.",
                               "Merge the two risks or differentiate them.", _src(rows[0])))
        else:
            signatures[sig] = risk
    return out


def check_02_unused_actions(d, today, s):
    """Function actions that no longer exist in the system or were never used (needs optional columns)."""
    rows = d["ruleset"]
    if not rows or ("action_in_system" not in rows[0] and "action_last_used" not in rows[0]):
        return None  # skipped: optional columns not supplied
    out, seen = [], set()
    cutoff = today - timedelta(days=s["unused_action_days"])
    for r in rows:
        key = (r["function_id"], r["action"])
        if key in seen:
            continue
        seen.add(key)
        if r.get("action_in_system", "").upper() in {"N", "NO"}:
            out.append(Finding(2, "Rule set", "Medium", f"{r['function_id']} / {r['action']}",
                               "Action no longer exists in the connected system.",
                               "Remove the action from the function.", _src(r)))
        elif "action_last_used" in r:
            lu = _d(r["action_last_used"])
            if lu is None or lu < cutoff:
                out.append(Finding(2, "Rule set", "Low", f"{r['function_id']} / {r['action']}",
                                   f"Action not used in the last {s['unused_action_days']} days.",
                                   "Confirm with the process owner whether it can be removed.", _src(r)))
    return out


def check_03_risk_owner_process(d, today, s):
    """Risks with no owner or no business-process mapping."""
    out, seen = [], set()
    for r in d["ruleset"]:
        if r["risk_id"] in seen or not _yes(r["risk_active"]):
            continue
        seen.add(r["risk_id"])
        gaps = [n for n, v in (("owner", r["risk_owner"]), ("business process", r["business_process"])) if not v]
        if gaps:
            out.append(Finding(3, "Rule set", "Medium", r["risk_id"],
                               f"Risk has no {' and no '.join(gaps)}.",
                               "Assign an accountable owner and business process.", _src(r)))
    return out


# ---------- Mitigating controls ----------

def check_04_control_owner(d, today, s):
    """Mitigating controls with no owner or an owner who has left."""
    m = d["mitigations"]
    if m is None:
        return None
    active = _active_users(d["users"])
    out, seen = [], set()
    for r in m:
        if r["control_id"] in seen:
            continue
        seen.add(r["control_id"])
        if not r["owner"]:
            out.append(Finding(4, "Controls", "High", r["control_id"], "Control has no owner.",
                               "Assign an owner who performs or signs off the control.", _src(r)))
        elif active is not None and r["owner"].upper() not in active:
            out.append(Finding(4, "Controls", "High", r["control_id"],
                               f"Owner {r['owner']} is not an active user (left or locked).",
                               "Reassign the control to a current owner.", _src(r)))
        mon = r.get("monitor", "")
        if active is not None and mon and mon.upper() not in active:
            out.append(Finding(4, "Controls", "Medium", f"{r['control_id']} monitor",
                               f"Monitor {mon} is not an active user (left or locked).",
                               "Assign a current monitor.", _src(r)))
    return out


def check_05_assignment_expiry(d, today, s):
    """Mitigation assignments expired or expiring within the window."""
    m = d["mitigations"]
    if m is None or not any(r.get("valid_to") for r in m):
        return None
    out, limit = [], today + timedelta(days=s["expiry_window_days"])
    for r in m:
        vt = _d(r["valid_to"])
        if vt is None:
            continue
        if vt < today:
            sev, txt = "High", f"expired on {vt.date()}"
        elif vt <= limit:
            sev, txt = "Medium", f"expires on {vt.date()}"
        else:
            continue
        out.append(Finding(5, "Controls", sev, f"{r['control_id']} -> {r['assigned_to']} ({r['risk_id']})",
                           f"Mitigation assignment {txt}; the risk " + ("is now unmitigated." if sev == "High" else "will become unmitigated."),
                           "Renew after review or remove the access.", _src(r)))
    return out


def check_06_never_evidenced(d, today, s):
    """Controls assigned but never evidenced (needs optional last_evidence_date column)."""
    m = d["mitigations"]
    if m is None or not m or "last_evidence_date" not in m[0]:
        return None
    out, seen = [], set()
    cutoff = today - timedelta(days=s["evidence_max_age_days"])
    for r in m:
        if r["control_id"] in seen:
            continue
        seen.add(r["control_id"])
        ev = _d(r["last_evidence_date"])
        if ev is None:
            out.append(Finding(6, "Controls", "High", r["control_id"], "Control has never been evidenced.",
                               "Run the control and record evidence, or retire it.", _src(r)))
        elif ev < cutoff:
            out.append(Finding(6, "Controls", "Medium", r["control_id"],
                               f"Last evidence on {ev.date()}, older than {s['evidence_max_age_days']} days.",
                               "Run the control and record evidence.", _src(r)))
    return out


# ---------- Emergency access ----------

def check_07_ff_too_many_users(d, today, s):
    """Firefighter IDs assigned to too many users."""
    ff = d["ff_setup"]
    if ff is None:
        return None
    users = {}
    for r in ff:
        users.setdefault(r["ff_id"], []).append(r)
    out = []
    for fid, rows in sorted(users.items()):
        n = len({r["assigned_user"] for r in rows})
        if n > s["max_users_per_ff_id"]:
            out.append(Finding(7, "Emergency", "High", fid,
                               f"Firefighter ID assigned to {n} users (limit {s['max_users_per_ff_id']}).",
                               "Reduce to the people who genuinely need emergency access.", _src(*rows[:3])))
    return out


def check_08_vague_reasons(d, today, s):
    """Emergency sessions with vague or missing reasons."""
    logs = d["ff_logs"]
    if logs is None:
        return None
    out = []
    for r in logs:
        t = r["reason_text"].strip()
        if not t or len(t) < s["min_reason_length"] or t.lower() in s["vague_reasons"]:
            out.append(Finding(8, "Emergency", "Medium", f"{r['ff_id']} session {r['session_id']}",
                               f"Reason missing or too vague: '{t}'." if t else "No reason given.",
                               "Require a ticket number and specific reason before logon.", _src(r)))
    return out


def check_09_late_review(d, today, s):
    """Emergency logs not reviewed within the agreed window."""
    logs = d["ff_logs"]
    if logs is None:
        return None
    out = []
    for r in logs:
        if r.get("review_status") is not None and "review_due" in r:
            due = _d(r["review_due"])
            if r["review_status"].strip().lower() not in {"finished", "closed", "approved", "completed"} and due and today > due:
                out.append(Finding(9, "Emergency", "High", f"{r['ff_id']} session {r['session_id']}",
                                   f"Log review request {r.get('review_request', '')} still open; due {due.date()}.",
                                   "Controller to review now.", _src(r)))
            continue
        lt, rv = _d(r["logon_time"]), _d(r["review_date"])
        if lt is None:
            continue
        due = lt + timedelta(days=s["review_window_days"])
        if rv is None and today > due:
            out.append(Finding(9, "Emergency", "High", f"{r['ff_id']} session {r['session_id']}",
                               f"Log not reviewed; due {due.date()}.", "Controller to review now.", _src(r)))
        elif rv is not None and rv > due:
            out.append(Finding(9, "Emergency", "Medium", f"{r['ff_id']} session {r['session_id']}",
                               f"Reviewed {(rv - lt).days} days after use (window {s['review_window_days']}).",
                               "Agree and enforce a review window.", _src(r)))
    return out


def check_10_self_review(d, today, s):
    """Controller reviewing their own emergency session (self-review)."""
    logs, ff = d["ff_logs"], d["ff_setup"]
    if logs is None and ff is None:
        return None
    out = [Finding(10, "Emergency", "High", f"{r['ff_id']} session {r['session_id']}",
                   f"User {r['ff_user']} reviewed their own emergency session.",
                   "Assign an independent controller.", _src(r))
           for r in logs or [] if r.get("reviewed_by") and r["reviewed_by"].upper() == r["ff_user"].upper()]
    seen = set()
    for r in ff or []:
        c = r.get("controller", "")
        if c and c.upper() == r["assigned_user"].upper() and (r["ff_id"], c) not in seen:
            seen.add((r["ff_id"], c))
            out.append(Finding(10, "Emergency", "High", f"{r['ff_id']} controller {c}",
                               f"{c} is both a firefighter and the controller of this ID, so can review their own sessions.",
                               "Assign a controller who cannot use this firefighter ID.", _src(r)))
    return out


def check_11_sensitive_actions(d, today, s):
    """Sensitive actions run during emergency sessions."""
    logs = d["ff_logs"]
    if logs is None:
        return None
    out = []
    for r in logs:
        hits = sorted({a.strip().upper() for a in r["actions"].replace(",", ";").split(";")} & s["sensitive_actions"])
        if hits:
            out.append(Finding(11, "Emergency", "Medium", f"{r['ff_id']} session {r['session_id']}",
                               f"Sensitive actions used: {', '.join(hits)}.",
                               "Controller to confirm each against the stated reason.", _src(r)))
    return out


def check_12_ff_owner_left(d, today, s):
    """Firefighter owners or controllers missing or no longer active."""
    ff = d["ff_setup"]
    active = _active_users(d["users"])
    if ff is None or active is None:
        return None
    out, seen = [], set()
    for r in ff:
        for role in ("owner", "controller"):
            who = r[role]
            key = (r["ff_id"], role, who)
            if key in seen:
                continue
            seen.add(key)
            if not who or who.upper() not in active:
                out.append(Finding(12, "Emergency", "High", f"{r['ff_id']} {role}",
                                   f"{role.title()} {who or '(blank)'} is missing or not an active user.",
                                   f"Assign a current {role}.", _src(r)))
    return out


CHECKS = [check_01_risk_functions, check_02_unused_actions, check_03_risk_owner_process,
          check_04_control_owner, check_05_assignment_expiry, check_06_never_evidenced,
          check_07_ff_too_many_users, check_08_vague_reasons, check_09_late_review,
          check_10_self_review, check_11_sensitive_actions, check_12_ff_owner_left]


def run_all(data, today=None, settings=None):
    """Return (findings, skipped) where skipped lists check numbers that lacked input."""
    today = today or datetime.combine(date.today(), datetime.min.time())
    s = {**SETTINGS, **(settings or {})}
    findings, skipped = [], []
    for i, fn in enumerate(CHECKS, start=1):
        res = fn(data, today, s)
        if res is None:
            skipped.append(i)
        else:
            findings.extend(res)
    order = {"High": 0, "Medium": 1, "Low": 2}
    findings.sort(key=lambda f: (order[f.severity], f.check_id, f.record))
    return findings, skipped
