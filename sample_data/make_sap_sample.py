"""Synthetic sample set in the layouts of the standard SAP Access Control reports.

Fictional company and people; headings only follow SAP's report layouts. Mixed date formats on purpose.
Run: python3 sample_data/make_sap_sample.py
"""
import csv
from pathlib import Path

OUT = Path(__file__).parent / "sap"
OUT.mkdir(exist_ok=True)


def write(name, header, rows):
    with (OUT / name).open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


RS = ["System", "Rule Set", "Access Risk ID", "Access Risk Description", "Access Risk Type", "Access Risk Level",
      "Business Process Description", "Functions", "Function Description", "Action", "Access Rule ID",
      "Permission Object", "Field", "Status", "Value From", "Value To", "Owner", "Condition"]
r = lambda risk, desc, lvl, bp, fn, act, obj, st, own: ["DEMO_ERP", "GLOBAL", risk, desc, "Segregation of Duties", lvl, bp, fn, fn + " function", act, "0001", obj, "TCD", st, act, "", own, "AND"]  # noqa: E731
write("access_rule_detail.csv", RS, [
    r("P001", "Create vendor and pay vendor", "High", "Procure to Pay", "PR01", "XK01", "S_TCODE", "Active", "AFINCH"),
    r("P001", "Create vendor and pay vendor", "High", "Procure to Pay", "PR01", "XK01", "F_LFA1_BUK", "Active", "AFINCH"),
    r("P001", "Create vendor and pay vendor", "High", "Procure to Pay", "PR02", "F110", "S_TCODE", "Active", "AFINCH"),
    r("P002", "Vendor and payment (old copy)", "High", "Procure to Pay", "PR01", "XK01", "S_TCODE", "Active", "AFINCH"),
    r("P002", "Vendor and payment (old copy)", "High", "Procure to Pay", "PR02", "F110", "S_TCODE", "Active", "AFINCH"),
    r("B010", "Maintain users and roles", "Critical", "", "BS09", "SU01", "S_TCODE", "InActive", ""),
])
write("mitigating_control_report.csv",
      ["OrgUnit Description", "Control ID", "Control Description", "Org Unit ID", "Approver", "Monitor", "Name",
       "Access Risk ID", "Access Risk Description", "Access Rule ID", "Access Risk Level", "System"], [
          ["DEMO FINANCE", "MC_P2P_01", "Monthly vendor change review", "10000001", "AFINCH", "DGRAY", "A Finch", "P001", "Create vendor and pay vendor", "*", "High", "DEMO_ERP"],
          ["DEMO IT", "MC_SEC_02", "Quarterly user admin log review", "10000002", "RTAYLOR", "OLEFT", "R Taylor", "B010", "Maintain users and roles", "*", "Critical", "DEMO_ERP"],
      ])
write("mitigated_object_report.csv", ["Control ID", "User ID", "Access Risk ID", "Valid From", "Valid To"], [
    ["MC_P2P_01", "JDOE", "P001", "01.01.2025", "31.12.2026"],
    ["MC_P2P_01", "KLEE", "P001", "01.01.2025", "30.09.2026"],
])
write("firefighter_ids.csv", ["Firefighter ID", "System", "Firefighter", "Owner", "Comments", "Last Updated", "Updated By", "Last Logon"],
      [["FF_FIN_01", "DEMO_ERP", u, "AFINCH", "", "6/1/2026", "ADMIN1", "10/30/2026"] for u in
       ["JDOE", "KLEE", "MPATEL", "SWONG", "TNGUYEN", "LBROWN"]]
      + [["FF_BASIS_01", "DEMO_ERP", "OKHAN", "RTAYLOR", "", "6/1/2026", "ADMIN1", "10/20/2026"],
         ["FF_BASIS_01", "DEMO_ERP", "DGRAY", "RTAYLOR", "", "6/1/2026", "ADMIN1", "10/20/2026"]])
write("controllers.csv", ["Controller", "Firefighter ID", "System", "Notification By", "Comments", "Last Updated", "Updated By"], [
    ["DGRAY", "FF_FIN_01", "DEMO_ERP", "Workflow", "", "6/1/2026", "ADMIN1"],
    ["DGRAY", "FF_BASIS_01", "DEMO_ERP", "Email", "", "6/1/2026", "ADMIN1"],
])
CL = ["Firefighter ID", "System", "Firefighter", "Date/Time", "Reason Code", "Owner", "Transaction", "Terminal",
      "Description", "Table Name", "Field Name", "Field Text", "Change Type", "Old Value", "New Value",
      "Reason code description", "Activity Description", "Program", "Additional Description", "Command",
      "Operating System", "OS Command", "Item Id", "Transaction Description", "Log Report", "Log Review Request"]
c = lambda ff, u, t, tx, act, add, req: [ff, "DEMO_ERP", u, t, "PROD_FIX", "AFINCH", tx, "T1", "", "", "", "", "", "", "", "Production fix", act, "", add, "", "", "", "", "", "", req]  # noqa: E731
write("consolidated_log_report.csv", CL, [
    c("FF_FIN_01", "JDOE", "10/1/2026 9:12:00 AM", "F110", "INC-48213 correct blocked payment run", "vendor 100245", "9000000101"),
    c("FF_FIN_01", "KLEE", "10/6/2026 10:40:00 PM", "SE16N", "fix", "", "9000000102"),
    c("FF_FIN_01", "KLEE", "10/6/2026 10:40:00 PM", "F110", "fix", "", "9000000102"),
    c("FF_BASIS_01", "OKHAN", "10/20/2026 7:55:00 AM", "SU01", "", "", "9000000103"),
])
write("log_review_requests.csv", ["Request", "Number/Key", "Request Type Description", "Priority Description",
                                  "Instance Status", "Instance Approval Status", "Created By", "On Hold By", "Due Date"], [
    ["9000000101", "9000000101", "Firefighter Log Review", "Medium", "Finished", "Approved", "DGRAY,D Gray (DGRAY)", "", "10/8/2026"],
    ["9000000102", "9000000102", "Firefighter Log Review", "Medium", "Finished", "Approved", "DGRAY,D Gray (DGRAY)", "", "10/13/2026"],
    ["9000000103", "9000000103", "Firefighter Log Review", "Medium", "Open", "", "DGRAY,D Gray (DGRAY)", "", "10/27/2026"],
])
write("suim_users.csv", ["User", "User Type", "Valid From", "Valid To", "Lock Status", "Last Logon"], [
    ["AFINCH", "Dialog", "01.01.2020", "31.12.9999", "", "03.11.2026"],
    ["DGRAY", "Dialog", "01.01.2020", "31.12.9999", "", "04.11.2026"],
    ["RTAYLOR", "Dialog", "01.01.2020", "31.08.2026", "", "29.08.2026"],
    ["OLEFT", "Dialog", "01.01.2020", "31.12.9999", "Locked by administrator", "01.02.2026"],
    ["JDOE", "Dialog", "01.01.2020", "31.12.9999", "", "01.11.2026"],
])
print("written to", OUT)
