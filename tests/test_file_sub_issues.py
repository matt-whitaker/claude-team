import unittest
from harness import HookCase

EPIC_BODY = ("## Sequencing\n\nOne story:\n\n- #1114 — the story.\n\n"
             "## Out of scope\n- superseded by #999\n")
LISTING = [
    {"number": 1114, "body": "**Branch: `1114-story`**", "user": {"type": "Bot"}},
    {"number": 1115, "body": "**Branch: `1114-story`**\n**Role: writer**", "user": {"type": "Bot"}},
    {"number": 1116, "body": "**Branch: `1114-story`**\n**Role: tester**", "user": {"type": "Bot"}},
    {"number": 999, "body": "unrelated", "user": {"type": "Bot"}},
]
ISSUES = {"1112": {"body": EPIC_BODY, "kids": []},
          "1114": {"body": "**Branch: `1114-story`**", "kids": []},
          "1115": {"body": "**Role: writer**"}, "1116": {"body": "**Role: tester**"},
          "999": {"body": "unrelated"}}


class FileSubIssues(HookCase):
    def file(self, issue, issues=ISSUES, listing=LISTING):
        return self.run_hook("file-sub-issues.py", {
            "ISSUE": issue, "GH_TOKEN": "t",
            "STUB_ISSUES": issues, "STUB_LISTING": listing,
        })

    def parented(self, r):
        pairs = []
        for c in self.calls_matching(r, "sub_issues", "POST"):
            url = next(a for a in c["args"] if "/sub_issues" in a)
            value = next(a for a in c["args"] if a.startswith("sub_issue_id="))
            pairs.append((url.split("/")[-2], value.split("=")[-1]))
        return pairs

    def test_an_epics_sequencing_section_is_its_anchor(self):
        r = self.file("1112")
        pairs = self.parented(r)
        self.assertIn(("1112", "11140"), pairs)

    def test_the_discovered_story_gets_its_own_tasks_one_level_down(self):
        r = self.file("1112")
        pairs = self.parented(r)
        self.assertIn(("1114", "11150"), pairs)
        self.assertIn(("1114", "11160"), pairs)

    def test_out_of_scope_references_are_never_adopted(self):
        r = self.file("1112")
        self.assertFalse([p for p in self.parented(r) if p[1] == "9990"])

    def test_a_story_trigger_parents_its_tasks(self):
        r = self.file("1114")
        pairs = self.parented(r)
        self.assertIn(("1114", "11150"), pairs)

    def test_a_pull_request_is_rejected_at_the_parenting_step(self):
        issues = dict(ISSUES)
        issues["1113"] = {"body": "", "pull_request": {"url": "x"}}
        body = EPIC_BODY.replace("- #1114 — the story.", "- #1114, #1113 — pair.")
        issues["1112"] = {"body": body, "kids": []}
        r = self.file("1112", issues=issues)
        self.assertFalse([p for p in self.parented(r) if p[1] == "11130"])
        self.assertIn("pull request, not an issue", r.stdout)


if __name__ == "__main__":
    unittest.main()
