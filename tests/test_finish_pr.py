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


class LandedWorkIsNotStranded(HookCase):
    """#44: `work-completion.py` lands the run's work on the story branch and the RUNNER's
    branch still carries the same commits, so `origin/<default>..HEAD` stays non-zero. This
    hook read that as stranded work — pushed the throwaway branch, opened a second PR for
    work that already had one coming, and told the reader their commits were safe on a ref
    that dies with the runner. Measured on run 32561656056: two `::error::` lines for one
    fault, and the louder one was the false one.

    `landed_ref` was already a `work-completion.py` output; the step was simply never given it."""

    STORY = {"43": {"body": "Branch: `43-give-story-and-task-colours`",
                    "title": "Give story and task their own colours"}}

    def finish(self, fx, **env):
        return self.run_hook("finish-pr.py", {
            "ISSUE": "43", "GH_TOKEN": "ghs_fixturetoken", "ROLES": "implementor",
            "STUB_ISSUES": self.STORY, "STUB_PRS": [], "STUB_LISTING": [],
            **env,
        }, cwd=fx.wc)

    def landed_run(self):
        """An as-is story: the run's own branch carries commits that are already on the
        story branch. Without LANDED_REF this is indistinguishable from stranded work."""
        fx = GitFixture(self._tmp)
        fx.checkout_new("claude/issue-43-20260822")
        fx.commit("labels.json", "recolour story and task")
        return fx

    def test_it_exits_quietly_and_names_where_the_work_actually_is(self):
        fx = self.landed_run()

        r = self.finish(fx, LANDED_REF="43-give-story-and-task-colours")

        self.assertEqual(r.returncode, 0)
        self.assertIn("43-give-story-and-task-colours", r.stdout)
        self.assertIn("not stranded", r.stdout)

    def test_it_does_not_push_the_runners_throwaway_branch(self):
        fx = self.landed_run()

        self.finish(fx, LANDED_REF="43-give-story-and-task-colours")

        self.assertNotIn("claude/issue-43", fx.origin_git("branch").stdout)

    def test_it_opens_no_second_pr(self):
        """open-story-pr.py owns the story's PR. A second one here splits the only review
        surface anyone reads, which is the thing one-PR-per-story exists to prevent."""
        fx = self.landed_run()

        r = self.finish(fx, LANDED_REF="43-give-story-and-task-colours")

        self.assertFalse(self.calls_matching(r, "pr", "create"))

    def test_it_never_calls_the_runners_branch_the_safe_one(self):
        """⚠️ The most dangerous thing this system can write is a message telling someone not
        to look further. `claude/issue-43-...` is never pushed and dies with the container."""
        fx = self.landed_run()

        r = self.finish(fx, LANDED_REF="43-give-story-and-task-colours")

        self.assertNotIn("claude/issue-43", r.stdout + r.stderr)

    def test_without_the_ref_the_stranded_recovery_still_fires(self):
        """The net under a genuinely stranded run is unchanged — LANDED_REF only ever
        distinguishes a landing from a loss, it does not switch the recovery off."""
        fx = self.landed_run()

        self.finish(fx)

        self.assertIn("claude/issue-43", fx.origin_git("branch").stdout)


if __name__ == "__main__":
    unittest.main()
