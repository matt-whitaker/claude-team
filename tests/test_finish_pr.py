import unittest
from harness import GitFixture, HookCase

UNSHAPED = {"1276": {"body": "Clean up the prose.", "title": "Cleanup Getting Started"}}


class StrandedCommits(HookCase):
    """A run that committed but never landed — the direct-handle path on an unshaped issue."""

    def finish(self, fx, **env):
        return self.run_hook("finish-pr.py", {
            "ISSUE": "1276", "GH_TOKEN": "t", "ROLES": "writer",
            "STUB_ISSUES": UNSHAPED, "STUB_PRS": [], "STUB_LISTING": [],
            **env,
        }, cwd=fx.wc)

    def test_the_orphan_branch_reaches_the_remote(self):
        fx = GitFixture(self._tmp)
        fx.checkout_new("1276-cleanup-getting-started")
        fx.commit("guide.astro", "voice pass")
        self.assertNotIn("1276-cleanup-getting-started", fx.origin_git("branch").stdout)

        self.finish(fx)

        self.assertIn("1276-cleanup-getting-started", fx.origin_git("branch").stdout)
        self.assertEqual(fx.ahead_of_mainline("1276-cleanup-getting-started"), 1)

    def test_a_failed_pr_fails_the_run_rather_than_reporting_success(self):
        fx = GitFixture(self._tmp)
        fx.checkout_new("1276-cleanup-getting-started")
        fx.commit("guide.astro", "voice pass")

        r = self.finish(fx, STUB_GH_FAIL=["pr create"])

        self.assertNotEqual(r.returncode, 0)
        self.assertIn("::error::", r.stdout + r.stderr)
        self.assertIn("safe on the remote", r.stdout + r.stderr)
        self.assertIn("1276-cleanup-getting-started", fx.origin_git("branch").stdout)

    def test_a_run_with_no_commits_still_exits_quietly(self):
        fx = GitFixture(self._tmp)
        fx.checkout_new("1276-cleanup-getting-started")

        r = self.finish(fx)

        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing to finish", r.stdout)
        self.assertNotIn("1276-cleanup-getting-started", fx.origin_git("branch").stdout)


if __name__ == "__main__":
    unittest.main()
