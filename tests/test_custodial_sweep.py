import unittest
from harness import HookCase

GOOD = "**Branch: `10-thing`**\n\n### Sequencing\n1. #11\n2. #12\n"
INERT = "**Branch: `10-thing`**\n\n### Sequencing\n\nIts tasks run in order: writer, then tester.\n"
NO_SECTION = "**Branch: `10-thing`**\n"


class Deliverable(HookCase):
    def sweep(self, body, role="architect", kind="story"):
        return self.run_hook("custodial-sweep.py", {
            "MODE": "deliverable", "ISSUE": "10", "ROLE": role, "KIND": kind,
            "GH_TOKEN": "t", "STUB_ISSUES": {"10": {"body": body}}})

    def test_an_inert_sequencing_section_is_reported_on_the_architect_run(self):
        r = self.sweep(INERT)
        self.assertIn("names no numbered refs", r.stderr + r.stdout)

    def test_it_warns_rather_than_failing_because_the_fallback_works(self):
        self.assertEqual(self.sweep(INERT).returncode, 0)

    def test_a_good_section_is_silent(self):
        self.assertNotIn("names no numbered refs", self.sweep(GOOD).stderr + self.sweep(GOOD).stdout)

    def test_no_section_is_silent(self):
        r = self.sweep(NO_SECTION)
        self.assertNotIn("names no numbered refs", r.stderr + r.stdout)

    def test_an_epic_is_exempt_because_its_section_has_a_looser_parser(self):
        # file-sub-issues reads any #N on any line of an epic's section, so prose is valid there
        r = self.sweep("### Sequencing\n\nStories: #11 then #12.\n", kind="epic")
        self.assertNotIn("names no numbered refs", r.stderr + r.stdout)

    def test_a_missing_branch_line_still_fails_the_run(self):
        r = self.sweep("### Sequencing\n1. #11\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no Branch line", r.stderr + r.stdout)


if __name__ == "__main__":
    unittest.main()
