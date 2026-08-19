import pathlib
import unittest

TEAM = (pathlib.Path(__file__).resolve().parent.parent / ".github/workflows/team.yml").read_text()
ACTION = (pathlib.Path(__file__).resolve().parent.parent / ".github/actions/load-prompt/action.yml").read_text()
STUB = (pathlib.Path(__file__).resolve().parent.parent / "templates/consumer-stub.yml").read_text()


class TeamWorkflow(unittest.TestCase):
    def test_is_a_reusable_workflow(self):
        self.assertIn("workflow_call:", TEAM)

    def test_no_origin_repo_paths_survive(self):
        self.assertNotIn("packages/claude-team", TEAM)
        self.assertNotIn("packages/claude-team", ACTION)

    def test_no_local_action_references(self):
        self.assertNotIn("uses: ./", TEAM)

    def test_no_origin_board_or_bots(self):
        self.assertNotIn('"@me"', TEAM)
        self.assertNotIn("brewdocs", TEAM)

    def test_the_board_and_bots_are_inputs(self):
        for needle in ("inputs.project_owner", "inputs.project_number", "inputs.allowed_bots"):
            self.assertIn(needle, TEAM)

    def test_assets_are_fetched_at_the_pinned_ref(self):
        self.assertIn("TEAM_REF", TEAM)
        self.assertIn('git clone -q --depth 1 --branch "$TEAM_REF"', TEAM)

    def test_the_overlay_is_the_consumer_convention(self):
        self.assertIn(".claude-team/setup.sh", TEAM)
        self.assertIn(".claude-team/prompts", ACTION)

    def test_no_comment_line_inside_if_blocks(self):
        lines = TEAM.split("\n")
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped.startswith("if: |"):
                continue
            indent = len(line) - len(stripped)
            for j in range(i + 1, len(lines)):
                nxt = lines[j]
                if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= indent:
                    break
                self.assertFalse(nxt.strip().startswith("#"),
                                 f"comment inside if block at line {j+1}")


if __name__ == "__main__":
    unittest.main()


class ReleasePins(unittest.TestCase):
    """Every pin that must move together at release time, asserted equal on every push.

    The pins: TEAM_REF (what the jobs clone), the remote refs on the two composite actions
    inside team.yml, load-prompt's default ref, and the stub template's @ref. A release that
    moves one without the rest ships a workflow fetching assets from a different version of
    itself — the drift this suite exists to make impossible."""

    def refs(self):
        import re
        team_ref = re.search(r"TEAM_REF: (\S+)", TEAM).group(1)
        action_refs = set(re.findall(r"uses: matt-whitaker/claude-team/[^@\n]+@(\S+)", TEAM))
        prompt_default = re.search(r"ref:\n    description[^\n]*\n    required: false\n    default: (\S+)", ACTION).group(1)
        stub_ref = re.search(r"uses: matt-whitaker/claude-team/\.github/workflows/team\.yml@(\S+)", STUB).group(1)
        return team_ref, action_refs, prompt_default, stub_ref

    def test_all_pins_agree(self):
        team_ref, action_refs, prompt_default, stub_ref = self.refs()
        self.assertEqual(action_refs, {team_ref})
        self.assertEqual(prompt_default, team_ref)
        self.assertEqual(stub_ref, team_ref)
