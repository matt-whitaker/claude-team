import unittest
from harness import HookCase

STORY = {"746": {"body": "**Branch: `746-backfill`**", "kids": []}}


class BranchNavigation(HookCase):
    def navigate(self, issue, issues, kind="story", exists=False, **extra):
        env = {"ISSUE": issue, "KIND": kind, "GH_TOKEN": "t", "STUB_ISSUES": issues,
               "STUB_HEAD_SHA": "a" * 40}
        if exists:
            env["STUB_GH_FAIL"] = []
        else:
            env["STUB_GH_FAIL"] = ["branches/746-backfill", "branches/1092-story"]
        env.update(extra)
        return self.run_hook("branch-navigation.py", env)

    def test_an_absent_branch_is_created_and_linked(self):
        r = self.navigate("746", STORY)
        self.assertTrue(self.calls_matching(r, "git/refs"))
        self.assertIn("created branch 746-backfill", r.stdout)

    def test_an_existing_branch_is_left_alone(self):
        r = self.navigate("746", STORY, exists=True)
        self.assertFalse(self.calls_matching(r, "git/refs", "POST"))
        self.assertIn("already exists", r.stdout)

    def test_an_epic_gets_no_branch(self):
        r = self.navigate("1112", {"1112": {"body": "", "kids": []}}, kind="epic")
        self.assertFalse(self.calls_matching(r, "git/refs"))
        self.assertIn("no branch", r.stdout)

    def test_a_spike_gets_no_branch(self):
        r = self.navigate("284", {"284": {"body": "", "kids": []}}, kind="spike")
        self.assertFalse(self.calls_matching(r, "git/refs"))

    def test_a_pr_trigger_is_a_noop(self):
        r = self.navigate("", STORY)
        self.assertIn("no branch to navigate", r.stdout)

    def test_a_missing_branch_line_warns_and_stops(self):
        r = self.navigate("9", {"9": {"body": "no line", "kids": []}})
        self.assertIn("::warning::", r.stdout)
        self.assertFalse(self.calls_matching(r, "git/refs"))


if __name__ == "__main__":
    unittest.main()
