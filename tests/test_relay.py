"""Core behaviour tests. Run with: ./relay selftest

These are the tests a self-edit must not break: policy, approval, idempotent sync,
promise recording, and the lesson loop. No network, no browser, temp databases only.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELAY = str(ROOT / "relay")
SNAPSHOT = str(ROOT / "examples" / "inbox-snapshot.json")


class RelayTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {**os.environ, "RELAY_DB": str(Path(self.tmp.name) / "test.db")}
        self.env.pop("RELAY_DRAFT_ONLY", None)
        self.cmd("init")
        self.cmd("seed-demo", "--reset")

    def tearDown(self):
        self.tmp.cleanup()

    def cmd(self, *args, input=None, ok=True):
        proc = subprocess.run(
            [sys.executable, RELAY, *args], env=self.env,
            input=input, text=True, capture_output=True,
        )
        if ok and proc.returncode != 0:
            self.fail(f"{args} failed ({proc.returncode}): {proc.stderr}\n{proc.stdout}")
        return proc

    def json(self, *args):
        return json.loads(self.cmd(*args).stdout)

    # ------------------------------------------------------------------ tests
    def test_queue_prioritises_churn_and_money(self):
        rows = self.json("queue", "--json")
        self.assertEqual([r["thread"] for r in rows], ["t-dana", "t-priya", "t-marcus"])
        self.assertTrue(any("churn" in r for r in rows[0]["reasons"]))

    def test_policy_blocks_sensitive_threads(self):
        out = self.json("check", "t-priya",
                        "--text", "The invoice is reissued and attached.")
        self.assertEqual(out["decision"], "requires_approval")
        self.assertIn("billing", " ".join(out["reasons"]).lower())

        out = self.json("check", "t-marcus",
                        "--text", "Here is the metadata and ACS URL.")
        self.assertEqual(out["decision"], "requires_approval")

    def test_approved_draft_sends_and_records_promise(self):
        self.cmd("draft", "t-marcus", "--text",
                 "Here is the metadata XML and ACS URL. SCIM is included on Growth.")
        self.cmd("approve", "1", "--by", "alex")
        out = json.loads(self.cmd(
            "send", "t-marcus", "--draft", "1", "--by", "agent",
            "--commit", "Send SAML metadata", "--commit-due", "1d",
        ).stdout)
        self.assertEqual(out["policy"]["decision"], "sent_after_approval")
        self.assertEqual(len(out["commitments"]), 1)

        thread = self.json("thread", "t-marcus")
        self.assertEqual(thread["messages"][-1]["direction"], "out")
        self.assertTrue(any(c["text"] == "Send SAML metadata" for c in thread["commitments"]))

    def test_consecutive_send_is_refused(self):
        self.cmd("draft", "t-marcus", "--text", "First.")
        self.cmd("approve", "1")
        self.cmd("send", "t-marcus", "--draft", "1")
        self.cmd("draft", "t-marcus", "--text", "Second.")
        self.cmd("approve", "2")
        second = self.cmd("send", "t-marcus", "--draft", "2", ok=False)
        self.assertEqual(second.returncode, 1)
        self.assertIn("already outbound", second.stderr)

    def test_sync_is_idempotent_and_spots_new_threads(self):
        first = json.loads(self.cmd("sync", SNAPSHOT).stdout)
        self.assertEqual([t["thread"] for t in first["new_threads"]], ["t-nadia"])
        self.assertEqual(len(first["new_messages"]), 2)

        second = json.loads(self.cmd("sync", SNAPSHOT).stdout)
        self.assertEqual(second["new_threads"], [])
        self.assertEqual(second["new_messages"], [])
        self.assertEqual(second["unchanged"], 3)

    def test_lesson_promotion_changes_loaded_identity(self):
        self.cmd("lesson", "add", "--scope", "voice", "--text",
                 "Open with one sentence that covers both asks.",
                 "--evidence", "t-priya")
        self.cmd("lesson", "promote", "1", "--by", "alex")
        soul = self.cmd("soul", "--with-lessons").stdout
        self.assertIn("Open with one sentence that covers both asks.", soul)

    def test_draft_only_env_blocks_send(self):
        self.cmd("draft", "t-marcus", "--text", "Draft only.")
        self.cmd("approve", "1")
        self.env["RELAY_DRAFT_ONLY"] = "1"
        blocked = self.cmd("send", "t-marcus", "--draft", "1", ok=False)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("RELAY_DRAFT_ONLY", blocked.stderr)


if __name__ == "__main__":
    unittest.main()
