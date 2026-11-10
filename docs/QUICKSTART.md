# Quick start: run the GRC Readiness Agent for SAP Access Control

One page, about 30 minutes. Everything runs on your own machine; nothing is uploaded and SAP is never changed.

## 1. Install (5 minutes)
You need Python 3.9 or later.
```
git clone https://github.com/murarijanka/sap-grc-agent.git
cd sap-grc-agent
pip3 install -r requirements.txt
```
Try it first with the built-in sample (a fictional company):
```
python3 run.py --sample
```
The PDF appears in `reports/`.

## 2. Export the reports from SAP Access Control (15 minutes)
Export each as **CSV**. Only the first is required; each extra report switches on more checks.

| # | Report | Where (Fiori launchpad) | Tip |
|---|---|---|---|
| 1 | Access Rule Detail | ARA Audit & Reporting | Filter by rule set; large rule sets may need background run |
| 2 | Mitigating Control Report | ARA Audit & Reporting | |
| 3 | Mitigated Object Report | ARA Audit & Reporting | Report By: User |
| 4 | Firefighter IDs | EAM Administration | Export the list |
| 5 | Controllers | EAM Administration | Export the list |
| 6 | Consolidated Log Report | EAM Reporting | Last 90 days |
| 7 | Log review requests | EAM Reporting > Search Requests | Same date range |
| 8 | User list | SUIM in each connected system | Include validity, lock status, last logon |

Saved as Excel? Open it and "Save As" CSV.

## 3. Run it (2 minutes)
**Upload screen** (easiest):
```
python3 -m streamlit run app.py
```
A browser page opens. Upload the CSVs, click **Run checks**, then **Download PDF report**.

**Or command line:**
```
python3 run.py --ruleset access_rule_detail.csv --controls mitigating_controls.csv --ff-ids firefighter_ids.csv --ff-controllers controllers.csv --ff-log consolidated_log.csv --ff-reviews log_reviews.csv --users users.csv --out reports/my-report.pdf
```

## 4. Read the report
- **Page 1:** counts by severity and the top 10 findings.
- **Findings by area:** each finding with the reason, a recommended action and the source file and row.
- **Appendix:** which checks ran or were skipped, and why.

Optional: plain-English explanations by Claude. Put an Anthropic API key in `~/.config/sap-grc-agent/key` and a model ID in `~/.config/sap-grc-agent/model`. User IDs are masked before anything is sent. Without them, the report works the same, minus the explanations.

## 5. Share feedback (no data, please)
Open a GitHub issue or message Murari Janka on LinkedIn: which findings were right, which were noise, what's missing, and any report that failed to load (column names only, never data).
