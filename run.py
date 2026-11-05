"""Command line: python3 run.py --sample   or   python3 run.py --ruleset r.csv [--mitigations m.csv ...] --out report.pdf"""
import argparse
from pathlib import Path

from grc_agent.checks import run_all
from grc_agent.loader import SCHEMAS, load_all
from grc_agent.report import build_pdf

ap = argparse.ArgumentParser()
ap.add_argument("--sample", action="store_true", help="use the synthetic sample data")
for name in SCHEMAS:
    ap.add_argument(f"--{name.replace('_', '-')}")
ap.add_argument("--out", default="reports/grc-readiness-report.pdf")
a = ap.parse_args()
paths = ({n: f"sample_data/{n}.csv" for n in SCHEMAS} if a.sample
         else {n: getattr(a, n) for n in SCHEMAS})
data = load_all(paths)
findings, skipped = run_all(data)
inputs = {n: (Path(p).name, len(data[n])) for n, p in paths.items() if p}
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
build_pdf(a.out, findings, skipped, inputs, org_name="Sample company (synthetic data)" if a.sample else "Your organisation")
print(f"{len(findings)} findings, {len(skipped)} checks skipped -> {a.out}")
