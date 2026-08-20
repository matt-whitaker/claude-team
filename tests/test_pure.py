import importlib.util
import os
import pathlib
import unittest

HOOKS = pathlib.Path(__file__).resolve().parent.parent / "hooks"
os.environ.setdefault("REPO", "o/r")
spec = importlib.util.spec_from_file_location("real_team", HOOKS / "team.py")
team = importlib.util.module_from_spec(spec)
spec.loader.exec_module(team)


class BranchLine(unittest.TestCase):
    def test_reads_the_backticked_branch(self):
        self.assertEqual(team.branch_line("**Branch: `746-x`**"), "746-x")

    def test_absent_is_empty(self):
        self.assertEqual(team.branch_line("no line here"), "")


class StoryFromBranch(unittest.TestCase):
    def test_leading_number_is_the_story(self):
        self.assertEqual(team.story_from_branch("1092-author-findings"), "1092")

    def test_failure_refs_derive_to_nothing(self):
        self.assertEqual(team.story_from_branch("failure/746-99-1"), "")

    def test_empty_and_none_are_safe(self):
        self.assertEqual(team.story_from_branch(""), "")


class RoleStamp(unittest.TestCase):
    def test_reads_the_stamp(self):
        self.assertEqual(team.role_stamp("**Role: writer**"), "writer")

    def test_absent_is_empty(self):
        self.assertEqual(team.role_stamp("**Branch: `1-x`**"), "")


class Scrub(unittest.TestCase):
    def test_removes_the_token(self):
        team.GH_TOKEN = "SEKRIT"
        self.assertNotIn("SEKRIT", team.scrub("https://x:SEKRIT@github.com/o/r"))

    def test_empty_token_is_identity(self):
        team.GH_TOKEN = ""
        self.assertEqual(team.scrub("abc"), "abc")


if __name__ == "__main__":
    unittest.main()

class RepairSchemaMatchesTheHook(unittest.TestCase):
    """The schema is what the model reads; the hook is what enforces. They must agree."""

    def test_every_classification_the_hook_accepts_is_offered_by_the_schema(self):
        import json, pathlib, re
        root = pathlib.Path(__file__).resolve().parent.parent
        hook = (root / "hooks/apply-repairs.py").read_text()
        allowed = set(re.search(r"CLASSIFICATION = \{([^}]*)\}", hook).group(1).replace('"', "").replace(" ", "").split(","))
        schema = json.dumps(json.load(open(root / "schemas/repairs.json")))
        missing = [label for label in allowed if label not in schema]
        self.assertEqual(missing, [], f"the hook accepts {missing} but the schema never mentions them")
