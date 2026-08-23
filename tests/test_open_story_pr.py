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


class AHandClosedTaskCanStillOpenTheStoryPR(HookCase):
    """⚠️ #31: THE ONE STALL WITH NO GESTURE TO RESUME IT.

    This hook had two call sites — after a landing, and the merge net — and both are events the
    machinery produces. A human closing the last task produces neither, so the story reached
    "every task closed, branch ahead, no PR" and stayed there permanently: re-adding the
    front-door label starts a TASK run, and the merge net passes the merged PR's base ref, which
    for a story that never got a PR never exists.

    Measured on a consumer at v1.1, on a three-task story whose tester run produced no handoff
    (#32): the task stayed open, the maintainer closed it by hand fourteen hours later, and
    nothing ran. Third story in that repo to need its PR opened by hand."""

    TASK = {
        "45": {"body": "Branch: `43-give-story-and-task-colours`\nRole: implementor"},
        "43": {
            "title": "Give story and task their own colours",
            "kids": [{"number": 45, "title": "Recolour", "state": "closed"}],
        },
    }

    _DEFAULT = object()

    def closed(self, issues=_DEFAULT, **env):
        # ⚠️ A sentinel, not `issues or self.TASK`. An EMPTY dict — the unreadable-issue case —
        # is falsy, so `or` silently substituted the healthy fixture and that test passed while
        # exercising nothing. Caught only because the hook then did the right thing for the
        # wrong input.
        if issues is self._DEFAULT:
            issues = self.TASK
        return self.run_hook("open-story-pr.py", {
            "ISSUE": "45", "GH_TOKEN": "ghs_fixturetoken",
            "STUB_ISSUES": issues, "STUB_PRS": [], "STUB_AHEAD": "1",
            **env,
        })

    def test_it_resolves_the_story_from_the_closed_tasks_branch_line(self):
        r = self.closed()

        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.calls_matching(r, "pr", "create",
                                            "43-give-story-and-task-colours"))

    def test_it_reads_the_branch_line_rather_than_taking_a_base(self):
        """The whole point of the third call site: the caller has an issue number, not a ref."""
        r = self.closed()
        self.assertIn("closed by hand", r.stdout)

    # ── the guard, which STARTS WORK and must therefore fail closed ────────
    def test_an_as_is_story_closed_by_hand_opens_nothing(self):
        """⚠️ Its Branch line names ITSELF, and nothing ever closes one from a run — GitHub
        closes it natively when its PR merges. So a hand-closed one is a maintainer abandoning
        it, and a PR saying `Closes #43` for an already-closed issue is the wrong answer."""
        as_is = {"43": {"title": "Worked as-is",
                        "body": "Branch: `43-give-story-and-task-colours`"}}
        r = self.run_hook("open-story-pr.py", {
            "ISSUE": "43", "GH_TOKEN": "ghs_fixturetoken",
            "STUB_ISSUES": as_is, "STUB_PRS": [], "STUB_AHEAD": "1",
        })

        self.assertEqual(r.returncode, 0)
        self.assertIn("not a task", r.stdout)
        self.assertFalse(self.calls_matching(r, "pr", "create"))

    def test_an_issue_with_no_branch_line_opens_nothing(self):
        """⚠️ Written negatively — "not a story, so proceed" — an unresolvable issue would open
        a PR. Written positively, only something recognised as a task can."""
        r = self.closed(issues={"45": {"body": "Just a thought I had."}})

        self.assertEqual(r.returncode, 0)
        self.assertIn("not a task", r.stdout)
        self.assertFalse(self.calls_matching(r, "pr", "create"))

    def test_an_unreadable_issue_opens_nothing(self):
        """`issue_body` returns empty for an issue the API could not read. A rate-limited minute
        must not open a PR against a ref derived from nothing."""
        r = self.closed(issues={})

        self.assertEqual(r.returncode, 0)
        self.assertFalse(self.calls_matching(r, "pr", "create"))

    # ── the existing guards still bound it ─────────────────────────────────
    def test_a_sibling_task_still_open_holds_the_pr_back(self):
        """The hook's own all-tasks-closed gate is what makes this call site safe to fire on
        EVERY hand-close rather than only the last one."""
        waiting = dict(self.TASK)
        waiting["43"] = {"title": "Colours", "kids": [
            {"number": 45, "state": "closed"}, {"number": 46, "state": "open"}]}
        r = self.closed(issues=waiting)

        self.assertEqual(r.returncode, 0)
        self.assertIn("still open", r.stdout)
        self.assertFalse(self.calls_matching(r, "pr", "create"))

    def test_an_existing_pr_is_not_duplicated(self):
        """Idempotence is what lets this share a hook with the merge net."""
        r = self.closed(STUB_PRS=[{"number": 99}])

        self.assertEqual(r.returncode, 0)
        self.assertIn("already open", r.stdout)
        self.assertFalse(self.calls_matching(r, "pr", "create"))

    def test_a_branch_that_is_not_ahead_opens_nothing(self):
        r = self.closed(STUB_AHEAD="0")

        self.assertEqual(r.returncode, 0)
        self.assertFalse(self.calls_matching(r, "pr", "create"))

    # ── the original call site is untouched ────────────────────────────────
    def test_base_still_wins_when_both_are_given(self):
        """The landing and merge paths pass BASE; nothing about them changes."""
        r = self.run_hook("open-story-pr.py", {
            "BASE": "43-give-story-and-task-colours", "ISSUE": "45",
            "GH_TOKEN": "ghs_fixturetoken", "STUB_ISSUES": self.TASK,
            "STUB_PRS": [], "STUB_AHEAD": "1",
        })

        self.assertEqual(r.returncode, 0)
        self.assertNotIn("closed by hand", r.stdout)
        self.assertTrue(self.calls_matching(r, "pr", "create"))


if __name__ == "__main__":
    unittest.main()
