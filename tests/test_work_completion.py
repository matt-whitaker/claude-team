import unittest
from harness import GitFixture, HookCase

TASK_ISSUES = {"1093": {"body": "**Branch: `1092-story`**", "title": "T"},
               "1092": {"body": "**Branch: `1092-story`**", "kids": [{"number": 1093}]}}
AS_IS_ISSUES = {"746": {"body": "**Branch: `746-backfill`**", "kids": []}}


class WorkCompletion(HookCase):
    def land(self, fx, issue, issues, handoff='{"remaining":[]}'):
        return self.run_hook("work-completion.py", {
            "ISSUE": issue, "HANDOFF": handoff, "GH_TOKEN": "t",
            "STUB_ISSUES": issues,
        }, cwd=fx.wc)

    def test_a_task_with_work_lands_closes_and_swaps_the_marker(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("1092-story")
        fx.checkout_new("1093-task")
        fx.commit("w.txt", "task work")
        r = self.land(fx, "1093", TASK_ISSUES)
        self.assertEqual(r.outputs.get("closed"), "true")
        self.assertEqual(fx.ahead_of_mainline("1092-story"), 1)
        self.assertTrue(self.calls_matching(r, "issue close 1093"))
        self.assertTrue([c for c in r.calls if c["kind"] == "mark_complete"])

    def test_no_commits_with_explicit_empty_remaining_closes(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("1092-story")
        fx.checkout_new("1093-task")
        r = self.land(fx, "1093", TASK_ISSUES)
        self.assertEqual(r.outputs.get("closed"), "true")
        self.assertIn("Nothing to do", " ".join(
            c["args"][1] for c in r.calls if c["kind"] == "upsert_comment"))

    def test_no_commits_with_no_handoff_stays_open(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("1092-story")
        fx.checkout_new("1093-task")
        r = self.land(fx, "1093", TASK_ISSUES, handoff="")
        self.assertEqual(r.outputs.get("closed"), "false")
        self.assertIn("author never reported", r.stdout)
        self.assertFalse(self.calls_matching(r, "issue close"))

    def test_no_commits_with_remaining_stays_open(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("1092-story")
        fx.checkout_new("1093-task")
        r = self.land(fx, "1093", TASK_ISSUES, handoff='{"remaining":["x"]}')
        self.assertEqual(r.outputs.get("closed"), "false")

    def test_unparseable_handoff_stays_open(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("1092-story")
        fx.checkout_new("1093-task")
        r = self.land(fx, "1093", TASK_ISSUES, handoff="{broken")
        self.assertEqual(r.outputs.get("closed"), "false")

    def test_as_is_story_lands_but_is_never_closed_here(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("746-backfill")
        fx.checkout_new("746-run")
        fx.commit("spec.md", "the spec")
        r = self.land(fx, "746", AS_IS_ISSUES)
        self.assertEqual(r.outputs.get("closed"), "false")
        self.assertEqual(fx.ahead_of_mainline("746-backfill"), 1)
        self.assertFalse(self.calls_matching(r, "issue close"))

    def test_a_stale_ancestor_ref_fast_forwards(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("746-backfill")
        for i in range(3):
            fx.commit(f"m{i}.txt", f"mainline moves {i}")
        fx.git("push", "-q", "origin", "mainline")
        fx.checkout_new("746-run")
        fx.commit("spec.md", "real work")
        r = self.land(fx, "746", AS_IS_ISSUES)
        self.assertIn("landed", r.stdout)
        self.assertGreaterEqual(fx.ahead_of_mainline("746-backfill"), 1)

    def test_a_race_reconciles_by_merge(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("1092-story")
        fx.checkout_new("1093-task")
        fx.commit("mine.txt", "my work")
        fx.git("checkout", "-q", "mainline")
        fx.checkout_new("sibling", "origin/1092-story")
        fx.commit("theirs.txt", "their work")
        fx.git("push", "-q", "origin", "sibling:1092-story")
        fx.git("checkout", "-q", "1093-task")
        r = self.land(fx, "1093", TASK_ISSUES)
        self.assertEqual(r.outputs.get("closed"), "true")
        self.assertIn("reconciling", r.stdout)
        self.assertEqual(fx.ahead_of_mainline("1092-story"), 3)

    def test_a_conflict_fails_with_unlandable(self):
        fx = GitFixture(self._tmp)
        fx.push_branch("1092-story")
        fx.checkout_new("1093-task")
        fx.commit("same.txt", "mine")
        fx.git("checkout", "-q", "mainline")
        fx.checkout_new("sibling2", "origin/1092-story")
        fx.commit("same.txt", "theirs")
        fx.git("push", "-q", "origin", "sibling2:1092-story")
        fx.git("checkout", "-q", "1093-task")
        r = self.land(fx, "1093", TASK_ISSUES)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.outputs.get("unlandable"), "true")


if __name__ == "__main__":
    unittest.main()
