"""Turn SAP report rows (grc_agent.sap) into the internal tables the checks use."""
from datetime import date

from .sap import read_report

UPLOADS = ["ruleset", "controls", "mitigated_objects", "ff_ids", "ff_controllers", "ff_log", "ff_reviews", "users"]
REQUIRED_UPLOADS = {"ruleset"}
DONE_STATUSES = {"finished", "closed", "approved", "completed", "decision taken"}


def _ruleset(rows):
    fn_active, seen, out = {}, set(), []
    for r in rows:
        if r.get("status", "Active").strip().lower() == "active":
            fn_active[r["function_id"]] = True
    for r in rows:
        key = (r["risk_id"], r["function_id"], r["action"])
        if key in seen:
            continue
        seen.add(key)
        out.append({**r, "risk_description": r.get("risk_description", ""), "risk_level": r.get("risk_level", ""),
                    "risk_owner": r.get("risk_owner", ""), "business_process": r.get("business_process", ""),
                    "risk_active": r.get("risk_active") or "Y",
                    "function_active": "Y" if fn_active.get(r["function_id"]) else "N"})
    return out


def _mitigations(controls, objects):
    out = [{**c, "control_description": c.get("control_description", ""), "monitor": c.get("monitor", ""),
            "assigned_to": "", "assignment_type": "", "valid_from": "", "valid_to": ""} for c in controls]
    info = {c["control_id"]: c for c in controls}
    for o in objects or []:
        c = info.get(o["control_id"], {})
        out.append({**o, "control_description": c.get("control_description", ""), "owner": c.get("owner", ""),
                    "monitor": c.get("monitor", ""), "risk_id": o.get("risk_id") or c.get("risk_id", ""),
                    "assignment_type": "", "valid_from": o.get("valid_from", "")})
    return out


def _ff_setup(ids, controllers):
    ctrl = {}
    for c in controllers or []:
        ctrl.setdefault(c["ff_id"], []).append(c)
    out = []
    for r in ids:
        for c in ctrl.get(r["ff_id"]) or [{"controller": ""}]:
            out.append({**r, "controller": c["controller"], "valid_to": "",
                        "_file": r["_file"] if c["controller"] == "" else f"{r['_file']} + {c['_file']}",
                        "_row": r["_row"] if c["controller"] == "" else f"{r['_row']} / {c['_row']}"})
    return out


def _ff_logs(log, reviews):
    rev = {r["request"]: r for r in reviews or []}
    sessions = {}
    for r in log:
        key = (r["ff_id"], r["ff_user"], r["logon_time"])
        s = sessions.setdefault(key, {**r, "session_id": f"{r['ff_user']} {r['logon_time']}", "actions": [],
                                      "reason_text": " ".join(x for x in (r.get("activity", ""), r.get("additional", "")) if x).strip(),
                                      "reviewed_by": "", "review_date": ""})
        if r.get("action"):
            s["actions"].append(r["action"])
        if r.get("review_request") and not s.get("review_request"):
            s["review_request"] = r["review_request"]
    out = []
    for s in sessions.values():
        s["actions"] = ";".join(sorted(set(s["actions"])))
        q = rev.get(s.get("review_request", ""))
        if q:
            s["review_status"], s["review_due"] = q.get("status", ""), q.get("due_date", "")
        out.append(s)
    return out


def _users(rows, today):
    out = []
    for r in rows:
        locked = r.get("status", "").strip()
        expired = r.get("valid_to") and r["valid_to"][:10] < today.isoformat()
        out.append({**r, "status": "Locked" if (locked and locked.lower() not in {"active", "not locked", "unlocked"}) or expired else "Active",
                    "valid_to": r.get("valid_to", ""), "last_logon": r.get("last_logon", "")})
    return out


def load_sap(paths, today=None):
    """paths: dict upload name -> CSV path. Returns the internal data dict for checks.run_all."""
    today = today or date.today()
    raw = {k: (read_report(p, k) if p else None) for k, p in ((k, paths.get(k)) for k in UPLOADS)}
    if raw["ruleset"] is None:
        raise ValueError("ruleset is required")
    return {
        "ruleset": _ruleset(raw["ruleset"]),
        "mitigations": _mitigations(raw["controls"], raw["mitigated_objects"]) if raw["controls"] else None,
        "ff_setup": _ff_setup(raw["ff_ids"], raw["ff_controllers"]) if raw["ff_ids"] else None,
        "ff_logs": _ff_logs(raw["ff_log"], raw["ff_reviews"]) if raw["ff_log"] else None,
        "users": _users(raw["users"], today) if raw["users"] else None,
        "_raw_counts": {k: (len(v) if v is not None else None) for k, v in raw.items()},
    }
