"""Each check must find exactly the issues planted in the sample data (as of 5 Nov 2026)."""
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from grc_agent.checks import run_all  # noqa: E402
from grc_agent.loader import load_all, UploadError, load_csv  # noqa: E402

S = ROOT / "sample_data"
TODAY = datetime(2026, 11, 5)
ALL = {n: S / f"{n}.csv" for n in ["ruleset", "mitigations", "ff_setup", "ff_logs", "users"]}


class TestChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.findings, cls.skipped = run_all(load_all(ALL), today=TODAY)

    def records(self, n):
        return sorted(f.record for f in self.findings if f.check_id == n)

    def test_nothing_skipped_with_full_set(self):
        self.assertEqual(self.skipped, [])

    def test_01(self):
        self.assertEqual(self.records(1), ["P002", "S010"])

    def test_02(self):
        self.assertEqual(self.records(2), ["F_GI_POST / VL02", "F_GI_POST / VL02N"])

    def test_03(self):
        self.assertEqual(self.records(3), ["S010"])

    def test_04(self):
        self.assertEqual(self.records(4), ["MC_O2C_03", "MC_SEC_02"])

    def test_05(self):
        self.assertEqual(self.records(5), ["MC_P2P_01 -> JDOE (P001)", "MC_P2P_01 -> KLEE (P001)"])

    def test_06(self):
        self.assertEqual(self.records(6), ["MC_O2C_03", "MC_SEC_02"])

    def test_07(self):
        self.assertEqual(self.records(7), ["FF_FIN_01"])

    def test_08(self):
        self.assertEqual(self.records(8), ["FF_BASIS_01 session 1003", "FF_FIN_01 session 1002"])

    def test_09(self):
        self.assertEqual(self.records(9), ["FF_BASIS_01 session 1003", "FF_FIN_01 session 1002"])

    def test_10(self):
        self.assertEqual(self.records(10), ["FF_FIN_01 session 1004"])

    def test_11(self):
        self.assertEqual(self.records(11), ["FF_BASIS_01 session 1003", "FF_FIN_01 session 1002"])

    def test_12(self):
        self.assertEqual(self.records(12), ["FF_BASIS_01 controller", "FF_BASIS_01 owner"])

    def test_every_finding_traces_to_a_row(self):
        for f in self.findings:
            self.assertTrue(f.source, f)

    def test_optional_files_skip_checks(self):
        _, skipped = run_all(load_all({"ruleset": ALL["ruleset"]}), today=TODAY)
        self.assertEqual(skipped, [4, 5, 6, 7, 8, 9, 10, 11, 12])

    def test_ruleset_required(self):
        with self.assertRaises(UploadError):
            load_all({})

    def test_wrong_columns_rejected(self):
        with self.assertRaises(UploadError):
            load_csv(ALL["users"], "ff_logs")


if __name__ == "__main__":
    unittest.main()
