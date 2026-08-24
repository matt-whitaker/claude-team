import unittest
from harness import HookCase

STORY_WITH_KIDS = {"1092": {"body": "**Branch: `1092-x`**", "kind": "story",
                            "kids": [{"number": 1093}, {"number": 1094}]}}
AS_IS = {"746": {"body": "**Branch: `746-x`**\n**Role: writer**", "kind": "story", "kids": []}}
TASK = {"1093": {"body": "**Branch: `1092-x`**\n**Role: writer**", "kind": "story", "kids": []}}
EPIC = {"1112": {"body": "", "kind": "epic", "kids": []}}


class Delegate(HookCase):
    def route(self, number, issues, comment="", event="issues", label="@claude"):
        return self.run_hook("delegate.py", {
            "NUMBER": number, "COMMENT_BODY": comment, "EVENT_NAME": event,
            "LABEL_NAME": label, "STUB_ISSUES": issues,
        })

    def line(self, r):
        return [l for l in r.stdout.splitlines() if l.startswith("roles=")][-1]

    def test_story_with_tasks_dispatches_and_runs_no_author(self):
        r = self.route("1092", STORY_WITH_KIDS)
        self.assertIn("roles= ", self.line(r))
        self.assertIn("dispatching its first wave", self.line(r))
        self.assertEqual(r.outputs.get("dispatch"), "true")

    def test_as_is_story_routes_to_its_stamped_author(self):
        r = self.route("746", AS_IS)
        self.assertIn("roles=writer", self.line(r))
        self.assertEqual(r.outputs.get("dispatch"), "false")

    def test_task_resolves_its_story_from_the_branch_line(self):
        r = self.route("1093", TASK)
        self.assertIn("roles=writer", self.line(r))
        self.assertIn("story=1092", self.line(r))

    def test_kind_is_resolved_on_the_handle_path(self):
        r = self.route("1112", EPIC, comment="@claude/architect please add a task",
                       event="issue_comment")
        self.assertIn("kind=epic", self.line(r))
        self.assertIn("roles=architect", self.line(r))

    def test_handle_on_a_story_still_resolves_context(self):
        r = self.route("746", AS_IS, comment="@claude/writer go", event="issue_comment")
        self.assertIn("roles=writer", self.line(r))
        self.assertIn("story=746", self.line(r))



    # ---- rule 1b: a bare mention settles to the root role, which bails (epic #78) ----

    def test_bare_mention_settles_to_the_root_role(self):
        r = self.route("1092", STORY_WITH_KIDS, comment="@claude what happened here?",
                       event="issue_comment", label="")
        self.assertIn("roles=claude", self.line(r))
        self.assertNotIn("consult", r.outputs, "delegate emits no consult output")
        self.assertIn("bails", self.line(r))

    def test_bare_mention_on_a_task_routes_to_the_custodian_diagnosis(self):
        r = self.route("1093", TASK, comment="@claude", event="issue_comment", label="")
        self.assertIn("roles=claude", self.line(r))
        self.assertIn("presumed stuck", self.line(r))

    def test_a_work_request_in_a_comment_reaches_no_working_role(self):
        r = self.route("1092", STORY_WITH_KIDS,
                       comment="@claude I believe this branch needs to be updated from its base",
                       event="issue_comment", label="")
        self.assertIn("roles=claude", self.line(r))
        self.assertEqual(r.outputs.get("dispatch"), "false",
                         "a comment must never start a wave")


if __name__ == "__main__":
    unittest.main()
