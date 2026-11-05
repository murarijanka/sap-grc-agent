"""Generate the synthetic sample set. Fictional company, fictional people; no real customer data.

Each file plants known issues so the demo shows every check. Run: python3 sample_data/make_sample.py
"""
import csv
from pathlib import Path

OUT = Path(__file__).parent


def write(name, header, rows):
    with (OUT / name).open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


write("ruleset.csv",
      ["risk_id", "risk_description", "risk_level", "risk_active", "risk_owner", "business_process",
       "function_id", "function_active", "action", "action_in_system", "action_last_used"],
      [
          ["P001", "Create vendor and pay vendor", "High", "Y", "AFINCH", "Procure to Pay", "F_VEND_MAINT", "Y", "XK01", "Y", "2026-10-30"],
          ["P001", "Create vendor and pay vendor", "High", "Y", "AFINCH", "Procure to Pay", "F_PAY_RUN", "Y", "F110", "Y", "2026-10-31"],
          ["P002", "Vendor maintenance and payment (old copy)", "High", "Y", "AFINCH", "Procure to Pay", "F_VEND_MAINT", "Y", "XK01", "Y", "2026-10-30"],
          ["P002", "Vendor maintenance and payment (old copy)", "High", "Y", "AFINCH", "Procure to Pay", "F_PAY_RUN", "Y", "F110", "Y", "2026-10-31"],
          ["S010", "Maintain users and roles", "Critical", "Y", "", "", "F_USER_ADM", "N", "SU01", "Y", "2026-11-01"],
          ["O005", "Create sales order and post goods issue", "Medium", "Y", "BCHEN", "Order to Cash", "F_SO_CREATE", "Y", "VA01", "Y", "2026-11-02"],
          ["O005", "Create sales order and post goods issue", "Medium", "Y", "BCHEN", "Order to Cash", "F_GI_POST", "Y", "VL02", "N", ""],
          ["O005", "Create sales order and post goods issue", "Medium", "Y", "BCHEN", "Order to Cash", "F_GI_POST", "Y", "VL02N", "Y", "2024-03-15"],
      ])

write("mitigations.csv",
      ["control_id", "control_description", "owner", "monitor", "assigned_to", "assignment_type",
       "risk_id", "valid_from", "valid_to", "last_evidence_date"],
      [
          ["MC_P2P_01", "Monthly review of vendor master changes", "AFINCH", "DGRAY", "JDOE", "User", "P001", "2025-01-01", "2026-12-31", "2026-10-05"],
          ["MC_P2P_01", "Monthly review of vendor master changes", "AFINCH", "DGRAY", "KLEE", "User", "P001", "2025-01-01", "2026-09-30", "2026-10-05"],
          ["MC_SEC_02", "Quarterly user admin log review", "RTAYLOR", "DGRAY", "Z_SEC_ADMIN", "Role", "S010", "2024-01-01", "2027-12-31", ""],
          ["MC_O2C_03", "Weekly sales order exception report", "", "BCHEN", "MPATEL", "User", "O005", "2025-06-01", "2028-06-30", "2025-02-10"],
      ])

ff_rows = [["FF_FIN_01", "AFINCH", "DGRAY", u, "2027-03-31"] for u in ["JDOE", "KLEE", "MPATEL", "SWONG", "TNGUYEN", "LBROWN", "PSINGH"]]
ff_rows += [["FF_BASIS_01", "RTAYLOR", "RTAYLOR", "OKHAN", "2027-03-31"],
            ["FF_BASIS_01", "RTAYLOR", "RTAYLOR", "EMILLER", "2027-03-31"]]
write("ff_setup.csv", ["ff_id", "owner", "controller", "assigned_user", "valid_to"], ff_rows)

write("ff_logs.csv",
      ["session_id", "ff_id", "ff_user", "logon_time", "reason_code", "reason_text", "actions", "reviewed_by", "review_date"],
      [
          ["1001", "FF_FIN_01", "JDOE", "2026-10-01 09:12", "PROD_FIX", "INC-48213 correct blocked payment run for vendor 100245", "F110;FBL1N", "DGRAY", "2026-10-03"],
          ["1002", "FF_FIN_01", "KLEE", "2026-10-06 22:40", "PROD_FIX", "fix", "SE16N;F110", "DGRAY", "2026-10-29"],
          ["1003", "FF_BASIS_01", "OKHAN", "2026-10-20 07:55", "BASIS", "", "SU01;PFCG", "", ""],
          ["1004", "FF_FIN_01", "DGRAY", "2026-10-22 14:05", "PROD_FIX", "INC-48877 reverse duplicate posting doc 5100009812", "FB08", "DGRAY", "2026-10-23"],
      ])

write("users.csv", ["user_id", "status", "valid_to", "last_logon"],
      [
          ["AFINCH", "Active", "9999-12-31", "2026-11-03"],
          ["BCHEN", "Active", "9999-12-31", "2026-11-04"],
          ["DGRAY", "Active", "9999-12-31", "2026-11-04"],
          ["RTAYLOR", "Locked", "2026-08-31", "2026-08-29"],
          ["JDOE", "Active", "9999-12-31", "2026-11-01"],
          ["KLEE", "Active", "9999-12-31", "2026-10-30"],
      ])
print("sample data written to", OUT)
