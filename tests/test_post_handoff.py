import unittest
from harness import HookCase

STORY = {"600": {"body": "Branch: `600-thing`"}}
HANDOFF = '{"commitMessage":"do it","remaining":[],"decisions":[],' \
          '"testingNotes":[],"docsCandidates":[]}'

ALL_SKIPPED = "implementor=skipped designer=skipped tester=skipped writer=skipped"
TESTER_RAN = "implementor=skipped designer=skipped tester=success writer=skipped"
TESTER_DIED = "implementor=skipped designer=skipped tester=failure writer=skipped"


class TheEmptyHandoffSaysWhichCaseItIs(HookCase):
    """⚠️ #32: ONE SENTENCE, FALSE IN THE CASE THAT ACTUALLY HALTS A STORY.

    It printed *"No handoff to post — no author ran, or its step failed."* Both halves are false
    when an author RAN and SUCCEEDED and returned nothing usable — so the one line a reader got
    sent them looking for a skipped job or a red step, neither of which existed. Measured on a
    consumer at v1.1: the tester step ran 2m27s and completed, HANDOFF was empty, every
    `closed`-gated step skipped, and the task sat open until a human closed it fourteen hours
    later — at which point nothing could open the story's PR at all (#31)."""

    def post(self, **env):
        return self.run_hook("post-handoff.py", {
            "GH_TOKEN": "ghs_fixturetoken", "STORY": "600", "ISSUE": "601",
            "STUB_ISSUES": STORY, **env,
        })

    # ── case 1: nobody ran ────────────────────────────────────────────────
    def test_no_author_ran_is_quiet_and_says_only_that(self):
        r = self.post(HANDOFF="", ROLES="", OUTCOMES=ALL_SKIPPED)

        self.assertEqual(r.returncode, 0)
        self.assertIn("no author ran", r.stdout)
        self.assertNotIn("::error::", r.stdout + r.stderr)

    def test_a_role_routed_but_never_started_counts_as_nobody_ran(self):
        """ROLES names who *should* run; the outcome says whether it did. A skipped step is not
        a role that ran, and treating it as one would report the wrong case."""
        r = self.post(HANDOFF="", ROLES="tester", OUTCOMES=ALL_SKIPPED)

        self.assertEqual(r.returncode, 0)
        self.assertIn("no author ran", r.stdout)

    # ── case 2: it ran and died ───────────────────────────────────────────
    def test_a_failed_step_is_named_and_not_double_reported(self):
        """The red step above is already the signal — reddening this one too would report one
        fault twice, which this package has paid for before."""
        r = self.post(HANDOFF="", ROLES="tester", OUTCOMES=TESTER_DIED)

        self.assertEqual(r.returncode, 0)
        self.assertIn("the tester step failure", r.stdout)
        self.assertNotIn("::error::", r.stdout + r.stderr)

    # ── case 3: it ran, succeeded, returned nothing ───────────────────────
    def test_a_successful_step_with_no_handoff_is_an_error(self):
        """⚠️ The task will not close and the story is halted. A plain line in a green run is
        how that stayed invisible."""
        r = self.post(HANDOFF="", ROLES="tester", OUTCOMES=TESTER_RAN)

        self.assertNotEqual(r.returncode, 0)
        self.assertIn("::error::", r.stdout + r.stderr)

    def test_it_names_the_role_and_contradicts_neither_half_of_the_old_sentence(self):
        r = self.post(HANDOFF="", ROLES="tester", OUTCOMES=TESTER_RAN)
        out = r.stdout + r.stderr

        self.assertIn("tester", out)
        self.assertIn("SUCCEEDED", out)
        self.assertIn("Nothing failed upstream", out)
        self.assertNotIn("no author ran, or its step failed", out)

    def test_it_says_what_will_happen_and_what_to_do(self):
        r = self.post(HANDOFF="", ROLES="tester", OUTCOMES=TESTER_RAN)
        out = r.stdout + r.stderr

        self.assertIn("will not close", out)
        self.assertIn("Re-trigger", out)

    def test_it_ungates_transcript_capture(self):
        """⚠️ WHY the step produced nothing is unknowable from anything else the run keeps, and
        on the run that produced #32 the toggle was off — the channel-with-no-reader failure
        landing on exactly the run that needed it. The caller ORs this into `enabled`."""
        r = self.post(HANDOFF="", ROLES="tester", OUTCOMES=TESTER_RAN)

        self.assertEqual(r.outputs.get("evidence"), "true")

    def test_the_other_two_cases_do_not_ungate_it(self):
        """Capture stays off where the toggle says off — a failed step already has its own
        ungated diagnosis, and a run where nothing started has nothing to capture."""
        for label, roles, outcomes in (
            ("nobody ran", "", ALL_SKIPPED),
            ("step failed", "tester", TESTER_DIED),
        ):
            with self.subTest(case=label):
                r = self.post(HANDOFF="", ROLES=roles, OUTCOMES=outcomes)
                self.assertNotIn("evidence", r.outputs)

    # ── the happy path is untouched ───────────────────────────────────────
    def test_a_real_handoff_still_posts_and_reddens_nothing(self):
        r = self.post(HANDOFF=HANDOFF, ROLES="tester", OUTCOMES=TESTER_RAN)

        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue([c for c in r.calls if c["kind"] == "upsert_comment"],
                        f"the handoff was not posted; calls={r.calls}")
        self.assertNotIn("evidence", r.outputs)


if __name__ == "__main__":
    unittest.main()
