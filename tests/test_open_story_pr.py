import unittest
from harness import HookCase

# One story, one task, the task closed — the state in which the hook is supposed to act.
READY = {
    "43": {
        "title": "Give story and task their own colours",
        "kids": [{"number": 45, "title": "Recolour the labels", "state": "closed"}],
    }
}


class ReportsWhyItCouldNotOpen(HookCase):
    """#27: the hook failed the run with 'open it by hand' and no cause. Every benign path
    returns earlier, so reaching the create and not creating anything is always a real fault —
    and the reader had nothing to act on."""

    def open_pr(self, **env):
        return self.run_hook("open-story-pr.py", {
            # ⚠️ A realistic token, not "t". `scrub()` is a plain replace, so a
            # one-character token rewrites every matching letter in gh's message and the
            # assertions below fail on the test's own fixture rather than the hook.
            "BASE": "43-give-story-and-task-colours", "GH_TOKEN": "ghs_fixturetoken",
            "STUB_ISSUES": READY, "STUB_PRS": [], "STUB_AHEAD": "1",
            **env,
        })

    def test_the_reason_gh_gave_reaches_the_log(self):
        r = self.open_pr(
            STUB_GH_FAIL=["pr create"],
            STUB_GH_STDERR="GraphQL: GitHub Actions is not permitted to create pull requests",
        )

        self.assertNotEqual(r.returncode, 0)
        self.assertIn("::error::", r.stdout + r.stderr)
        self.assertIn("not permitted to create pull requests", r.stdout + r.stderr)

    def test_it_names_the_two_causes_worth_checking(self):
        r = self.open_pr(STUB_GH_FAIL=["pr create"])

        self.assertIn("Settings -> Actions -> General", r.stdout + r.stderr)
        self.assertIn("pull-requests: write", r.stdout + r.stderr)

    def test_a_silent_failure_still_says_something_rather_than_nothing(self):
        r = self.open_pr(STUB_GH_FAIL=["pr create"], STUB_GH_STDERR="")

        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no reason reported", r.stdout + r.stderr)

    def test_the_token_never_reaches_the_report(self):
        """⚠️ `gh` echoes the remote URL in its errors and the token rides in it. Actions masks
        the LOG only, and this text is one edit away from being posted on an issue."""
        r = self.open_pr(
            GH_TOKEN="ghs_supersecret",
            STUB_GH_FAIL=["pr create"],
            STUB_GH_STDERR="fatal: https://x-access-token:ghs_supersecret@github.com/o/r denied",
        )

        self.assertNotIn("ghs_supersecret", r.stdout + r.stderr)
        self.assertIn("***", r.stdout + r.stderr)

    def test_the_success_path_is_unchanged(self):
        r = self.open_pr()

        self.assertEqual(r.returncode, 0)
        self.assertIn("opened the story PR", r.stdout)
        self.assertTrue(self.calls_matching(r, "pr", "create"))

    def test_a_branch_that_is_not_ahead_returns_before_the_create(self):
        """The benign paths must keep returning quietly — the failure above is loud precisely
        because nothing legitimate reaches it."""
        r = self.open_pr(STUB_AHEAD="0")

        self.assertEqual(r.returncode, 0)
        self.assertFalse(self.calls_matching(r, "pr", "create"))

    def test_an_open_task_holds_the_pr_back(self):
        waiting = {"43": {"title": "Colours", "kids": [{"number": 45, "state": "open"}]}}
        r = self.open_pr(STUB_ISSUES=waiting)

        self.assertEqual(r.returncode, 0)
        self.assertIn("still open", r.stdout)
        self.assertFalse(self.calls_matching(r, "pr", "create"))


if __name__ == "__main__":
    unittest.main()
