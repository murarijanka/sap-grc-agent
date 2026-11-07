"""Upload screen: python3 -m streamlit run app.py

Files are processed in memory on this machine; nothing is stored or sent anywhere.
"""
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from grc_agent.checks import run_all
from grc_agent.adapt import load_sap
from grc_agent.sap import SapFormatError, read_report
from grc_agent.report import build_pdf

ROOT = Path(__file__).parent

# Tooltips: which standard SAP report to export. Menu paths confirmed in SAP Access Control 12.0 Fiori.
UPLOADS = {
    "ruleset": ("1. Access Rule Detail (required)",
                "Fiori launchpad > ARA Audit & Reporting > Access Rule Detail. Filter by rule set (and risk IDs if large), "
                "run in foreground or background, then Export to CSV."),
    "controls": ("2. Mitigating Control Report",
                 "ARA Audit & Reporting > Mitigation Control Report. Export to CSV. Gives approver and monitor per control."),
    "mitigated_objects": ("3. Mitigated Object Report",
                          "ARA Audit & Reporting > Mitigated Object Report, Report By: User. Export to CSV. "
                          "Gives validity dates per assignment (layout still to confirm with a pilot)."),
    "ff_ids": ("4. Firefighter IDs",
               "EAM Administration > Firefighter IDs. Export the list to CSV: firefighter ID, firefighter, owner."),
    "ff_controllers": ("5. Controllers",
                       "EAM Administration > Controllers. Export the list to CSV: controller per firefighter ID."),
    "ff_log": ("6. Consolidated Log Report",
               "EAM Reporting > Consolidated Log Report for a date range (e.g. last 90 days). Export to CSV."),
    "ff_reviews": ("7. Log review requests",
                   "EAM Reporting > Search Requests, request type firefighter log review, same date range. Export to CSV."),
    "users": ("8. User list (SUIM)",
              "In each connected SAP system: SUIM user list with validity, lock status and last logon. Export to CSV."),
}
SAMPLE = {"ruleset": "access_rule_detail.csv", "controls": "mitigating_control_report.csv",
          "mitigated_objects": "mitigated_object_report.csv", "ff_ids": "firefighter_ids.csv",
          "ff_controllers": "controllers.csv", "ff_log": "consolidated_log_report.csv",
          "ff_reviews": "log_review_requests.csv", "users": "suim_users.csv"}

st.set_page_config(page_title="SAP GRC Readiness Agent", page_icon="🛡️", layout="centered")
st.title("SAP GRC Readiness Agent")
st.caption("Read-only checks on SAP Access Control exports. Nothing is stored or sent anywhere: "
           "files are processed on this machine. People decide every fix.")

use_sample = st.toggle("Try with sample data (synthetic company)", value=False)

paths, errors, inputs = {}, [], {}
tmp = Path(tempfile.mkdtemp(prefix="grc_"))
for name, (label, tip) in UPLOADS.items():
    if use_sample:
        p = ROOT / "sample_data" / "sap" / SAMPLE[name]
        st.text_input(label, value=p.name, disabled=True, help=tip)
    else:
        f = st.file_uploader(label, type=["csv"], help=tip, key=name)
        if not f:
            continue
        p = tmp / f.name
        p.write_bytes(f.getvalue())
    try:
        rows = read_report(p, name)
        paths[name] = p
        inputs[name] = (p.name, len(rows))
    except SapFormatError as e:
        errors.append(str(e))

for e in errors:
    st.error(e)

ready = "ruleset" in paths and not errors
if st.button("Run checks", type="primary", disabled=not ready):
    data = load_sap(paths)
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
