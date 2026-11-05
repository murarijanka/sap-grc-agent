# SAP GRC Readiness Agent (Level 1)

A free, open tool that reads standard SAP Access Control exports and reports governance gaps before a migration off GRC 12.0. It is read-only: it never logs in to SAP and never changes SAP.

**Status:** early build. The 12 checks and sample data are done; the PDF report, upload screen and Claude explanations are next.

## How it works
- 12 checks run as fixed, tested Python rules. AI never decides a finding.
- Each finding is traced to the source file and row.
- Claude (planned) writes plain-English explanations from the findings only, with user IDs masked.

## Try it
```
python3 sample_data/make_sample.py
python3 -m unittest discover -s tests -v
```

The sample data is synthetic: a fictional company and fictional people.

## Credits
Designed and directed by Murari Janka, founder of MyOmniCareer. Built with Claude (Anthropic).

## Licence
Apache 2.0. See LICENSE and NOTICE.

SAP and SAP Access Control are trademarks of SAP SE. This project is independent and not affiliated with or endorsed by SAP SE.
