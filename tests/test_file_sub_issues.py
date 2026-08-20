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


# ── #23: an epic's run must not adopt its stories' tasks ────────────────────────────────
#
# Numbers and bodies are the brewdocs.beer#1269 incident: story #1290 with tasks #1291 and
# #1292, each carrying prose that legitimately names the epic. The epic's Sequencing section
# names only the story.
EPIC_1269 = "## Sequencing\n\n1. #1290 — the guide.\n"
NESTED = [
    {"number": 1290, "user": {"type": "Bot"},
     "body": "**Branch: `1290-guide-backup`**\n\nA story under epic #1269."},
    {"number": 1291, "user": {"type": "Bot"},
     "body": "**Branch: `1290-guide-backup`**\n**Role: writer**\n\n"
             "Story #1290, under epic #1269. Follows story #1270."},
    {"number": 1292, "user": {"type": "Bot"},
     "body": "**Branch: `1290-guide-backup`**\n**Role: implementor**\n\n"
             "Part of epic #1269; already live, from epic #947."},
]
NESTED_ISSUES = {
    "1269": {"body": EPIC_1269, "kids": []},
    "1290": {"body": NESTED[0]["body"], "kids": []},
    "1291": {"body": NESTED[1]["body"]},
    "1292": {"body": NESTED[2]["body"]},
}


class Nesting(HookCase):
    def file(self, issue):
        return self.run_hook("file-sub-issues.py", {
            "ISSUE": issue, "GH_TOKEN": "t",
            "STUB_ISSUES": NESTED_ISSUES, "STUB_LISTING": NESTED,
        })

    def parented(self, r):
        pairs = []
        for c in self.calls_matching(r, "sub_issues", "POST"):
            url = next(a for a in c["args"] if "/sub_issues" in a)
            value = next(a for a in c["args"] if a.startswith("sub_issue_id="))
            pairs.append((url.split("/")[-2], value.split("=")[-1]))
        return pairs

    def test_the_story_reaches_its_epic(self):
        self.assertIn(("1269", "12900"), self.parented(self.file("1269")))

    def test_the_epic_does_not_adopt_its_storys_tasks(self):
        pairs = self.parented(self.file("1269"))
        self.assertNotIn(("1269", "12910"), pairs)
        self.assertNotIn(("1269", "12920"), pairs)

    def test_the_tasks_reach_their_own_story(self):
        pairs = self.parented(self.file("1269"))
        self.assertIn(("1290", "12910"), pairs)
        self.assertIn(("1290", "12920"), pairs)


if __name__ == "__main__":
    unittest.main()
