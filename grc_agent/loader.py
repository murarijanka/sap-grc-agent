"""Load the five upload files (CSV) into lists of dicts, keeping the source row number."""
import csv
from pathlib import Path

# Upload field -> required columns. Optional files may be missing; their checks are skipped.
SCHEMAS = {
    "ruleset": ["risk_id", "risk_description", "risk_level", "risk_active", "risk_owner",
                "business_process", "function_id", "function_active", "action"],
    "mitigations": ["control_id", "control_description", "owner", "monitor", "assigned_to",
                    "assignment_type", "risk_id", "valid_from", "valid_to"],
    "ff_setup": ["ff_id", "owner", "controller", "assigned_user", "valid_to"],
    "ff_logs": ["session_id", "ff_id", "ff_user", "logon_time", "reason_code", "reason_text",
                "actions", "reviewed_by", "review_date"],
    "users": ["user_id", "status", "valid_to", "last_logon"],
}
REQUIRED_UPLOADS = {"ruleset"}


class UploadError(ValueError):
    pass


DATE_COLUMNS = {"valid_from", "valid_to", "last_logon", "logon_time", "review_date",
                "last_evidence_date", "action_last_used"}
DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")


def _valid_date(v):
    from datetime import datetime
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(v, fmt)
            return True
        except ValueError:
            pass
    return False


def load_csv(path, name):
    """Return rows as dicts with '_row' = line number in the file (header is line 1)."""
    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = [c.strip() for c in (reader.fieldnames or [])]
        missing = [c for c in SCHEMAS[name] if c not in cols]
        if missing:
            raise UploadError(f"{name}: missing required columns {missing}")
        rows = []
        for i, raw in enumerate(reader, start=2):
            row = {k.strip(): (v or "").strip() for k, v in raw.items() if k}
            row["_row"] = i
            row["_file"] = path.name
            for c in DATE_COLUMNS & row.keys():
                if row[c] and not _valid_date(row[c]):
                    raise UploadError(f"{name}: row {i}, column {c}: '{row[c]}' is not a date (use YYYY-MM-DD)")
            rows.append(row)
    return rows


def load_all(paths):
    """paths: dict upload-name -> file path (or None). Returns dict name -> rows or None."""
    data = {}
    for name in SCHEMAS:
        p = paths.get(name)
        if not p:
            if name in REQUIRED_UPLOADS:
                raise UploadError(f"{name} is required")
            data[name] = None
            continue
        data[name] = load_csv(p, name)
    return data
