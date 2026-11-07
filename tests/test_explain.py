"""Masking: no real user ID may appear in what is sent to Claude, and placeholders map back exactly."""
import sys
import unittest
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from grc_agent.adapt import load_sap  # noqa: E402
from grc_agent.checks import run_all  # noqa: E402
from grc_agent.explain import collect_user_ids, mask, unmask  # noqa: E402
from tests.test_sap import PATHS  # noqa: E402


class TestMask(unittest.TestCase):
    def test_no_user_ids_leak(self):
        data = load_sap(PATHS, today=date(2026, 11, 5))
        findings, _ = run_all(data, today=datetime(2026, 11, 5))
        ids = collect_user_ids(data)
        masked, mapping = mask(findings, ids)
        sent = " ".join(m["record"] + " " + m["finding"] for m in masked)
        for uid in ids:
            self.assertNotRegex(sent, rf"\b{uid}\b")
        self.assertTrue(mapping)
        self.assertEqual(unmask("U1 and U2", mapping), f"{mapping['U1']} and {mapping['U2']}")


if __name__ == "__main__":
    unittest.main()
