"""Command line: python3 run.py --sample   or   python3 run.py --ruleset r.csv [--mitigations m.csv ...] --out report.pdf"""
import argparse
from pathlib import Path

from grc_agent.checks import run_all
from grc_agent.adapt import UPLOADS, load_sap
from grc_agent.report import build_pdf

ap = argparse.ArgumentParser()
ap.add_argument("--sample", action="store_true", help="use the synthetic sample data")
for name in UPLOADS:
    ap.add_argument(f"--{name.replace('_', '-')}")
ap.add_argument("--out", default="reports/grc-readiness-report.pdf")
a = ap.parse_args()
SAMPLE = {"ruleset": "access_rule_detail.csv", "controls": "mitigating_control_report.csv",
          "mitigated_objects": "mitigated_object_report.csv", "ff_ids": "firefighter_ids.csv",
          "ff_controllers": "controllers.csv", "ff_log": "consolidated_log_report.csv",
          "ff_reviews": "log_review_requests.csv", "users": "suim_users.csv"}
paths = ({n: f"sample_data/sap/{f}" for n, f in SAMPLE.items()} if a.sample
         else {n: getattr(a, n) for n in UPLOADS})
data = load_sap(paths)
findings, skipped = run_all(data)
inputs = {n: (Path(p).name, data['_raw_counts'][n]) for n, p in paths.items() if p}
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
build_pdf(a.out, findings, skipped, inputs, org_name="Sample company (synthetic data)" if a.sample else "Your organisation")
print(f"{len(findings)} findings, {len(skipped)} checks skipped -> {a.out}")
