"""Plain-English explanations written by Claude. Optional: the report works without it.

Claude never decides a finding. It only receives the findings the fixed rules produced, with every
user ID replaced by a placeholder (U1, U2, ...), and returns a short explanation for each.

Setup (on the machine that runs the tool):
  ~/.config/sap-grc-agent/key    the Anthropic API key (chmod 600)
  ~/.config/sap-grc-agent/model  the exact Claude model ID to use, chosen by the owner
"""
import json
import re
import urllib.request
from pathlib import Path

CONF = Path.home() / ".config" / "sap-grc-agent"
API_URL = "https://api.anthropic.com/v1/messages"
USER_FIELDS = ("user_id", "risk_owner", "owner", "monitor", "assigned_user", "controller", "ff_user",
               "assigned_to", "reviewed_by")


def _read(name):
    p = CONF / name
    return p.read_text().strip() if p.exists() else ""


def collect_user_ids(data):
    ids = set()
    for rows in data.values():
        if isinstance(rows, list):
            for r in rows:
                for f in USER_FIELDS:
                    v = (r.get(f) or "").strip()
                    if v:
                        ids.add(v)
    return ids


def mask(findings, user_ids):
    """Return (masked list of dicts, mapping placeholder -> real ID). Longest IDs replaced first."""
    mapping, rev = {}, {}
    pattern = re.compile(r"\b(" + "|".join(re.escape(u) for u in sorted(user_ids, key=len, reverse=True)) + r")\b") if user_ids else None

    def sub(text):
        if not pattern:
            return text
        def rep(m):
            uid = m.group(1)
            if uid not in rev:
                rev[uid] = f"U{len(rev) + 1}"
                mapping[rev[uid]] = uid
            return rev[uid]
        return pattern.sub(rep, text)

    out = [{"n": i, "check": f.check_id, "area": f.area, "severity": f.severity,
            "record": sub(f.record), "finding": sub(f.reason)} for i, f in enumerate(findings)]
    return out, mapping


def unmask(text, mapping):
    for ph, uid in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"\b{re.escape(ph)}\b", uid, text)
    return text


PROMPT = """You write short, plain-English explanations for an SAP GRC Access Control readiness report.
Fixed rules already decided every finding below; do not add, remove, dispute or re-rate findings, and do not invent facts.
User IDs are masked as U1, U2...; keep the placeholders exactly as given.
For each finding, write 1-2 sentences for a GRC lead or auditor: why it matters and the risk if it is migrated as-is.
Then write a 3-sentence summary of the overall picture.
Reply with JSON only: {"summary": "...", "explanations": [{"n": 0, "text": "..."}, ...]}

Findings:
"""


def explain(findings, data, timeout=60):
    """Return (summary, {index: explanation}) or (None, {}) when not configured or on any error."""
    key, model = _read("key"), _read("model")
    if not key or not model or not findings:
        return None, {}
    masked, mapping = mask(findings, collect_user_ids(data))
    body = json.dumps({"model": model, "max_tokens": 4000,
                       "messages": [{"role": "user", "content": PROMPT + json.dumps(masked, indent=1)}]}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = json.loads(r.read())["content"][0]["text"]
        text = text[text.find("{"): text.rfind("}") + 1]
        parsed = json.loads(text)
        exps = {int(e["n"]): unmask(e["text"], mapping) for e in parsed.get("explanations", [])
                if 0 <= int(e["n"]) < len(findings)}
        return unmask(parsed.get("summary", ""), mapping) or None, exps
    except Exception:
        return None, {}
