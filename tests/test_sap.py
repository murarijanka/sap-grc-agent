"""SAP-layout sample: mapping, mixed date formats, and the findings each check should raise."""
import sys
import unittest
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from grc_agent.adapt import load_sap  # noqa: E402
from grc_agent.checks import run_all  # noqa: E402
from grc_agent.sap import SapFormatError, read_report, to_iso, user_id  # noqa: E402

S = ROOT / "sample_data" / "sap"
FILES = {"ruleset": "access_rule_detail.csv", "controls": "mitigating_control_report.csv",
         "mitigated_objects": "mitigated_object_report.csv", "ff_ids": "firefighter_ids.csv",
         "ff_controllers": "controllers.csv", "ff_log": "consolidated_log_report.csv",
         "ff_reviews": "log_review_requests.csv", "users": "suim_users.csv"}
PATHS = {k: S / v for k, v in FILES.items()}


class TestFormats(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(to_iso("6/15/2022"), "2022-06-15")
        self.assertEqual(to_iso("15.06.2022"), "2022-06-15")
        self.assertEqual(to_iso("10/6/2026 10:40:00 PM"), "2026-10-06 22:40:00")

    def test_user_id(self):
        self.assertEqual(user_id("GRC300-00,Training (GRC300-00)"), "GRC300-00")
        self.assertEqual(user_id("ACMITAPP00"), "ACMITAPP00")

    def test_wrong_report_rejected(self):
        with self.assertRaises(SapFormatError):
            read_report(PATHS["ff_controllers"], "ruleset")


class TestChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = load_sap(PATHS, today=date(2026, 11, 5))
        cls.f, cls.skipped = run_all(data, today=datetime(2026, 11, 5))

    def rec(self, n):
        return sorted(x.record for x in self.f if x.check_id == n)

    def test_skipped(self):
        self.assertEqual(self.skipped, [2, 6])  # no usage data, no evidence/frequency in standard exports

    def test_01_duplicate_and_inactive(self):
        self.assertEqual(self.rec(1), ["B010", "P002"])

    def test_03_no_owner_or_process(self):
        self.assertEqual(self.rec(3), ["B010"])

    def test_04_owner_and_monitor(self):
        self.assertEqual(self.rec(4), ["MC_SEC_02", "MC_SEC_02 monitor"])

    def test_05_expiry(self):
        self.assertEqual(self.rec(5), ["MC_P2P_01 -> JDOE (P001)", "MC_P2P_01 -> KLEE (P001)"])

    def test_07_too_many(self):
        self.assertEqual(self.rec(7), ["FF_FIN_01"])

    def test_08_vague(self):
        self.assertEqual(len(self.rec(8)), 2)

    def test_09_open_review(self):
        self.assertEqual(len(self.rec(9)), 1)

    def test_10_controller_is_firefighter(self):
        self.assertEqual(self.rec(10), ["FF_BASIS_01 controller DGRAY"])

    def test_11_sensitive(self):
        self.assertEqual(len(self.rec(11)), 2)

    def test_12_owner_left(self):
        self.assertEqual(self.rec(12), ["FF_BASIS_01 owner"])


if __name__ == "__main__":
    unittest.main()
