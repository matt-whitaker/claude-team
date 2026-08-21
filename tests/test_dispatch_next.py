import unittest
from harness import HookCase

BODY_WAVES = "### Sequencing\n1. #11\n2. #12, #13 — parallel\n3. #14\n"
TASKS4 = [{"number": 11, "state": "closed"}, {"number": 12, "state": "open"},
          {"number": 13, "state": "open"}, {"number": 14, "state": "open"}]


def issues(body, tasks, labelled=()):
    data = {"10": {"body": body, "state": "OPEN", "kids": tasks}}
    for t in tasks:
        data[str(t["number"])] = {
            "body": "**Role: writer**",
            "labels": (["@claude"] if t["number"] in labelled else []),
        }
    return data


class DispatchNext(HookCase):
    def dispatch(self, body, tasks, labelled=(), extra=None):
        env = {"STORY": "10", "GH_TOKEN": "t",
               "STUB_ISSUES": issues(body, tasks, labelled)}
        env.update(extra or {})
        return self.run_hook("dispatch-next.py", env)

    def dispatched(self, r):
        return [c["args"][1].split("/")[-2] for c in self.calls_matching(r, "labels")]

    def test_parallel_wave_dispatches_together(self):
        r = self.dispatch(BODY_WAVES, TASKS4)
        self.assertEqual(self.dispatched(r), ["12", "13"])

    def test_in_flight_task_is_skipped_not_redispatched(self):
        r = self.dispatch(BODY_WAVES, TASKS4, labelled=(12,))
        self.assertEqual(self.dispatched(r), ["13"])

    def test_no_section_dispatches_one_in_derived_order(self):
        r = self.dispatch("plain body", TASKS4)
        self.assertEqual(self.dispatched(r), ["12"])

    def test_forgotten_task_is_appended_never_stranded(self):
        tasks = [{"number": 11, "state": "closed"}, {"number": 12, "state": "closed"},
                 {"number": 14, "state": "open"}]
        r = self.dispatch("### Sequencing\n1. #11\n2. #12\n", tasks)
        self.assertEqual(self.dispatched(r), ["14"])

    def test_all_closed_defers_to_the_story_pr(self):
        tasks = [{"number": 11, "state": "closed"}]
        r = self.dispatch("x", tasks)
        self.assertIn("every task of #10 is closed", r.stdout)

    def test_completion_label_does_not_read_as_in_flight(self):
        data = issues("x", [{"number": 11, "state": "open"}])
        data["11"]["labels"] = ["@claude/complete"]
        r = self.run_hook("dispatch-next.py",
                          {"STORY": "10", "GH_TOKEN": "t", "STUB_ISSUES": data})
        self.assertEqual(self.dispatched(r), ["11"])

    def test_secrets_present_but_no_token_is_loud(self):
        r = self.run_hook("dispatch-next.py",
                          {"STORY": "10", "HAVE_SECRETS": "true", "GH_TOKEN": ""})
        self.assertIn("::error::", r.stdout)
        self.assertIn("not INSTALLED", r.stdout)

    def test_no_secrets_is_quiet(self):
        r = self.run_hook("dispatch-next.py",
                          {"STORY": "10", "HAVE_SECRETS": "false", "GH_TOKEN": ""})
        self.assertIn("::notice::", r.stdout)
        self.assertNotIn("::error::", r.stdout)


# ── #28: a section that parses to zero refs must say so ─────────────────────────────────
PROSE = "### Sequencing\n\nIts tasks run in order: writer, then implementor, then tester.\n"
HEADING_LINE = "**Sequencing.** Its tasks run in order: #11, then #12, then #14.\n"


class InertSequencing(HookCase):
    def dispatch(self, body, tasks=TASKS4):
        return self.run_hook("dispatch-next.py", {
            "STORY": "10", "GH_TOKEN": "t", "STUB_ISSUES": issues(body, tasks)})

    def dispatched(self, r):
        return [c["args"][1].split("/")[-2] for c in self.calls_matching(r, "labels")]

    def test_prose_section_warns_rather_than_falling_back_in_silence(self):
        r = self.dispatch(PROSE)
        self.assertIn("Sequencing section but no numbered refs", r.stderr + r.stdout)

    def test_refs_on_the_heading_line_are_unreachable_and_warn(self):
        # the form the Architect prompt used to demonstrate: refs present, none parseable
        r = self.dispatch(HEADING_LINE)
        self.assertIn("Sequencing section but no numbered refs", r.stderr + r.stdout)

    def test_the_fallback_itself_is_kept(self):
        self.assertEqual(self.dispatched(self.dispatch(PROSE)), ["12"])

    def test_no_section_at_all_stays_silent(self):
        # absent is legitimate and documented — only a section that says nothing is a problem
        r = self.dispatch("plain body")
        self.assertNotIn("Sequencing section but no numbered refs", r.stderr + r.stdout)

    def test_a_good_section_stays_silent(self):
        r = self.dispatch(BODY_WAVES)
        self.assertNotIn("Sequencing section but no numbered refs", r.stderr + r.stdout)

    def test_a_foreign_ref_still_warns_on_its_own_terms(self):
        r = self.dispatch("### Sequencing\n1. #999\n2. #12\n")
        self.assertIn("#999, which is not one of #10's tasks", r.stderr + r.stdout)
        self.assertNotIn("no numbered refs", r.stderr + r.stdout)


if __name__ == "__main__":
    unittest.main()
