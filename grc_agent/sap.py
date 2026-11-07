"""Read standard SAP Access Control report exports (CSV) and convert them to the tool's internal rows.

Column names come from the standard reports' headings. Layouts marked UNVERIFIED have not yet been
confirmed against a real export and accept likely alternatives.
"""
import csv
import re
from datetime import datetime
from pathlib import Path

DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y", "%d.%m.%Y %H:%M:%S",
                "%d.%m.%Y %H:%M", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M",
                "%Y%m%d")


def to_iso(value):
    """Return YYYY-MM-DD[ HH:MM:SS] for any SAP date format seen so far, or '' if blank. Raises ValueError."""
    v = (value or "").strip()
    if not v or v in {"00000000", "00.00.0000", "99991231"}:
        return "" if v != "99991231" else "9999-12-31"
    for fmt in DATE_FORMATS:
        try:
            d = datetime.strptime(v, fmt)
            return d.strftime("%Y-%m-%d %H:%M:%S" if ("%H" in fmt or "%I" in fmt) else "%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError(f"'{v}' is not a recognised date")


_ID_IN_BRACKETS = re.compile(r"\(([^()]+)\)\s*$")


def user_id(value):
    """'GRC300-00,Training (GRC300-00)' -> 'GRC300-00'; plain IDs pass through."""
    v = (value or "").strip()
    m = _ID_IN_BRACKETS.search(v)
    if m:
        return m.group(1).strip()
    return v.split(",")[0].strip()


def _norm(h):
    return re.sub(r"[^a-z0-9]", "", (h or "").lower())


# Report -> {internal field: [accepted SAP headings]}
REPORTS = {
    "ruleset": {  # Access Rule Detail Report (verified)
        "risk_id": ["Access Risk ID"], "risk_description": ["Access Risk Description"],
        "risk_level": ["Access Risk Level"], "risk_owner": ["Owner"],
        "business_process": ["Business Process Description", "Business Process"],
        "function_id": ["Functions", "Function"], "action": ["Action"], "status": ["Status"],
        "risk_active": ["Risk Status", "Access Risk Status"],  # optional, not in standard layout
    },
    "controls": {  # Mitigating Control Report (verified)
        "control_id": ["Control ID", "Mitigating Control ID"], "control_description": ["Control Description"],
        "owner": ["Approver"], "monitor": ["Monitor"], "risk_id": ["Access Risk ID"],
        "frequency_days": ["Frequency in Days"],  # optional
        "last_evidence_date": ["Last Evidence Date"],  # optional, not in Access Control
    },
    "mitigated_objects": {  # Mitigated Object Report (UNVERIFIED: no data in training system)
        "control_id": ["Control ID", "Mitigating Control ID", "Mitigating Control"],
        "assigned_to": ["User ID", "User", "Role", "Role Name", "Profile", "Object"],
        "risk_id": ["Access Risk ID", "Risk ID"], "valid_from": ["Valid From", "From Date"],
        "valid_to": ["Valid To", "To Date"],
    },
    "ff_ids": {  # EAM Administration > Firefighter IDs (verified)
        "ff_id": ["Firefighter ID"], "assigned_user": ["Firefighter"], "owner": ["Owner"],
        "last_logon": ["Last Logon"],
    },
    "ff_controllers": {  # EAM Administration > Controllers (verified)
        "ff_id": ["Firefighter ID"], "controller": ["Controller"], "notification_by": ["Notification By"],
    },
    "ff_log": {  # Consolidated Log Report (verified)
        "ff_id": ["Firefighter ID"], "ff_user": ["Firefighter"], "logon_time": ["Date/Time"],
        "reason_code": ["Reason Code"], "activity": ["Activity Description"],
        "additional": ["Additional Description"], "action": ["Transaction"],
        "review_request": ["Log Review Request"], "owner": ["Owner"],
    },
    "ff_reviews": {  # Search Requests, log review requests (verified)
        "request": ["Request", "Number/Key"], "status": ["Instance Status"],
        "approval_status": ["Instance Approval Status"], "due_date": ["Due Date"],
        "request_type": ["Request Type Description"],
    },
    "users": {  # SUIM user list (UNVERIFIED headings)
        "user_id": ["User", "User ID", "User Name"], "status": ["Lock Status", "Status", "Locked"],
        "valid_to": ["Valid To", "Valid through"], "last_logon": ["Last Logon", "Last Logon Date", "Logon Date"],
    },
}
REQUIRED = {
    "ruleset": ["risk_id", "function_id", "action"], "controls": ["control_id", "owner", "risk_id"],
    "mitigated_objects": ["control_id", "assigned_to", "valid_to"], "ff_ids": ["ff_id", "assigned_user"],
    "ff_controllers": ["ff_id", "controller"], "ff_log": ["ff_id", "ff_user", "logon_time"],
    "ff_reviews": ["request", "status"], "users": ["user_id"],
}
DATE_FIELDS = {"valid_from", "valid_to", "logon_time", "due_date", "last_logon", "last_evidence_date"}
USER_FIELDS = {"risk_owner", "owner", "monitor", "assigned_user", "controller", "ff_user", "user_id"}


class SapFormatError(ValueError):
    pass


def read_report(path, kind):
    """Read one SAP export. Returns rows with internal field names plus _file and _row."""
    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        delim = ";" if sample.count(";") > sample.count(",") and sample.count(";") > sample.count("\t") else (
            "\t" if sample.count("\t") > sample.count(",") else ",")
        reader = csv.reader(fh, delimiter=delim)
        header = next(reader, [])
        idx = {_norm(h): i for i, h in enumerate(header)}
        colmap = {}
        for field, names in REPORTS[kind].items():
            for n in names:
                if _norm(n) in idx and idx[_norm(n)] not in colmap.values():
                    colmap[field] = idx[_norm(n)]
                    break
        missing = [f for f in REQUIRED[kind] if f not in colmap]
        if missing:
            want = [REPORTS[kind][f][0] for f in missing]
            raise SapFormatError(f"{kind}: missing columns {want}. Found: {header}")
        rows = []
        for i, raw in enumerate(reader, start=2):
            if not any(c.strip() for c in raw):
                continue
            row = {f: (raw[c].strip() if c < len(raw) else "") for f, c in colmap.items()}
            for f in DATE_FIELDS & row.keys():
                try:
                    row[f] = to_iso(row[f])
                except ValueError as e:
                    raise SapFormatError(f"{kind}: row {i}, {REPORTS[kind][f][0]}: {e}") from None
            for f in USER_FIELDS & row.keys():
                row[f] = user_id(row[f])
            row["_file"], row["_row"] = path.name, i
            rows.append(row)
    return rows
