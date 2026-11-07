"""Upload screen: python3 -m streamlit run app.py

Files are processed in memory on this machine; nothing is stored or sent anywhere.
"""
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from grc_agent.checks import run_all
from grc_agent.loader import SCHEMAS, UploadError, load_csv
from grc_agent.report import build_pdf

ROOT = Path(__file__).parent

# Tooltips: how to export each file. SAP menu paths are TO VERIFY in a sandbox before release.
UPLOADS = {
    "ruleset": ("1. Risk rule set (required)",
                "Export the active rule set with risks, functions and actions "
                "(Access Control: Access Risk Analysis > rule set reports; path to verify). "
                "Optional extra columns: action_in_system, action_last_used. Usually run by the GRC administrator."),
    "mitigations": ("2. Mitigating controls and assignments",
                    "Export the standard mitigating controls report with control ID, owner, monitor, "
                    "assignments and valid-from/valid-to dates (path to verify). "
                    "Optional: last_evidence_date. Usually run by the GRC administrator or controls owner."),
    "ff_setup": ("3. Emergency access setup",
                 "Export firefighter IDs with owners, controllers and assigned users "
                 "(Emergency Access Management reports; path to verify)."),
    "ff_logs": ("4. Emergency access logs and reasons",
                "Export firefighter log summaries for a date range (e.g. last 90 days) with reason, "
                "actions used, reviewer and review date (path to verify)."),
    "users": ("5. User list",
              "Export users with status, validity dates and last logon from each connected SAP system "
              "(e.g. SUIM user list). Last logon is not held in GRC."),
}

st.set_page_config(page_title="SAP GRC Readiness Agent", page_icon="🛡️", layout="centered")
st.title("SAP GRC Readiness Agent")
st.caption("Read-only checks on SAP Access Control exports. Nothing is stored or sent anywhere: "
           "files are processed on this machine. People decide every fix.")

use_sample = st.toggle("Try with sample data (synthetic company)", value=False)

paths, errors, inputs = {}, [], {}
tmp = Path(tempfile.mkdtemp(prefix="grc_"))
for name, (label, tip) in UPLOADS.items():
    if use_sample:
        p = ROOT / "sample_data" / f"{name}.csv"
        st.text_input(label, value=p.name, disabled=True, help=tip)
    else:
        f = st.file_uploader(label, type=["csv"], help=tip, key=name)
        if not f:
            continue
        p = tmp / f.name
        p.write_bytes(f.getvalue())
    try:
        rows = load_csv(p, name)
        paths[name] = p
        inputs[name] = (p.name, len(rows))
    except UploadError as e:
        errors.append(str(e))

for e in errors:
    st.error(e)

ready = "ruleset" in paths and not errors
if st.button("Run checks", type="primary", disabled=not ready):
    from grc_agent.loader import load_all
    data = load_all(paths)
    findings, skipped = run_all(data)
    sev = {s: sum(f.severity == s for f in findings) for s in ("High", "Medium", "Low")}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("High", sev["High"]); c2.metric("Medium", sev["Medium"])
    c3.metric("Low", sev["Low"]); c4.metric("Checks skipped", len(skipped))
    if skipped:
        st.info(f"Skipped checks (input not supplied): {', '.join(map(str, skipped))}")
    st.dataframe([{"Severity": f.severity, "Area": f.area, "Record": f.record, "Reason": f.reason,
                   "Source": "; ".join(f.source)} for f in findings], use_container_width=True, hide_index=True)
    out = tmp / "grc-readiness-report.pdf"
    build_pdf(out, findings, skipped, inputs,
              org_name="Sample company (synthetic data)" if use_sample else "Your organisation")
    st.download_button("Download PDF report", out.read_bytes(),
                       file_name=f"grc-readiness-report-{datetime.now():%Y%m%d}.pdf", mime="application/pdf")
elif not ready and not errors:
    st.caption("Upload at least the risk rule set, or switch on sample data.")

st.divider()
st.caption("Designed and directed by Murari Janka, built with Claude (Anthropic). Apache 2.0. "
           "Not affiliated with SAP SE.")
