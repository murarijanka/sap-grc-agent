# GRC Readiness Agent for SAP Access Control (Level 1)

A free, open tool that reads standard SAP Access Control 12.0 report exports and reports governance gaps before a migration to GRC for SAP HANA. It is read-only: it never logs in to SAP and never changes SAP. People decide every fix.

**Status:** early build. 12 checks, SAP report mapping, PDF report and upload screen work on synthetic data. Pilot testing on real exports is next; plain-English explanations by Claude are coming.

**See a sample report:** [docs/sample-report.pdf](docs/sample-report.pdf) (synthetic company; explanations written by Claude from the findings).

## How it works
- 12 checks run as fixed, tested Python rules. AI never decides a finding.
- Each finding is traced to the source file and row.
- Runs locally. Customer data never leaves the machine.

## What to upload (CSV exports of standard reports)
| # | Report | Where in SAP Access Control (Fiori) | Required |
|---|---|---|---|
| 1 | Access Rule Detail | ARA Audit & Reporting | Yes |
| 2 | Mitigating Control Report | ARA Audit & Reporting | No |
| 3 | Mitigated Object Report | ARA Audit & Reporting | No |
| 4 | Firefighter IDs | EAM Administration | No |
| 5 | Controllers | EAM Administration | No |
| 6 | Consolidated Log Report | EAM Reporting | No |
| 7 | Log review requests (Search Requests) | EAM Reporting | No |
| 8 | User list (SUIM) | Each connected SAP system | No |

Missing files skip their checks; the report lists what was skipped. Several date formats (YYYY-MM-DD, DD.MM.YYYY, M/D/YYYY) and "ID,Name (ID)" user fields are handled.

## Try it
```
pip3 install -r requirements.txt
python3 sample_data/make_sap_sample.py
python3 -m unittest discover -s tests -v
python3 run.py --sample              # PDF in reports/
python3 -m streamlit run app.py      # upload screen
```
The sample data is synthetic: a fictional company and fictional people, laid out like the SAP reports.

## Credits
Designed and directed by Murari Janka, founder of MyOmniCareer. Built with Claude (Anthropic).

## Licence
Apache 2.0. See LICENSE and NOTICE.

SAP and SAP Access Control are trademarks of SAP SE. This project is independent and not affiliated with or endorsed by SAP SE.
