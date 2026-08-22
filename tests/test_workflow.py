import pathlib
import unittest

TEAM = (pathlib.Path(__file__).resolve().parent.parent / ".github/workflows/team.yml").read_text()
ACTION = (pathlib.Path(__file__).resolve().parent.parent / ".github/actions/load-prompt/action.yml").read_text()
STUB = (pathlib.Path(__file__).resolve().parent.parent / "templates/consumer-stub.yml").read_text()
SELF = (pathlib.Path(__file__).resolve().parent.parent / ".github/workflows/claude.yml").read_text()


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

    def test_every_author_step_carries_the_handoff_schema(self):
        self.assertEqual(TEAM.count("--json-schema '${{ steps.schema.outputs.body }}'"), 4)

    def test_handoff_reads_every_author_step(self):
        handoffs = [l for l in TEAM.splitlines() if "HANDOFF:" in l and "steps." in l]
        self.assertEqual(len(handoffs), 3)
        for line in handoffs:
            for step in ("implementor", "designer", "tester", "writer"):
                self.assertIn(f"steps.{step}.outputs.structured_output", line)

    def test_only_the_delegate_checkout_drops_credentials(self):
        lines = TEAM.splitlines()
        settings = [i for i, l in enumerate(lines) if l.strip() == "persist-credentials: false"]
        self.assertEqual(len(settings), 1)
        self.assertLess(settings[0], lines.index("  architect:"))

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


class ReadmeDocumentsEveryInput(unittest.TestCase):
    """⚠️ THE README TABLE IS A SECOND COPY OF THE WORKFLOW'S CONTRACT, so it drifts by default.

    A consumer reads it to decide what to paste. A secret the workflow starts consuming and the
    table never mentions is a feature nobody knows to enable — and every optional secret here
    fails *silently*, so nothing else would ever surface the omission.

    Both directions, because each has its own failure: undocumented means a feature nobody
    switches on, invented means a maintainer hunting for a secret that does nothing.
    """

    def setUp(self):
        import re
        root = pathlib.Path(__file__).resolve().parent.parent
        self.readme = (root / "README.md").read_text()
        self.secrets = set(re.findall(r"secrets\.([A-Z_]+)", TEAM)) - {"GITHUB_TOKEN"}
        self.vars = set(re.findall(r"vars\.([A-Z_]+)", TEAM))
        self.inputs = set(re.findall(r"^      ([a-z_]+):$", TEAM.split("jobs:")[0], re.M))
        self.assertIn("## Inputs and secrets", self.readme, "the reference section is gone")
        self.section = self.readme.split("## Inputs and secrets")[1]

    def test_every_secret_the_workflow_reads_is_documented(self):
        self.assertTrue(self.secrets)
        for name in sorted(self.secrets):
            with self.subTest(secret=name):
                self.assertTrue(f"`{name}`" in self.readme,
                                f"{name} is read by team.yml but absent from the README table")

    def test_every_repository_variable_is_documented(self):
        self.assertTrue(self.vars)
        for name in sorted(self.vars):
            with self.subTest(var=name):
                self.assertTrue(f"`{name}`" in self.readme,
                                f"{name} is read by team.yml but absent from the README table")

    def test_every_workflow_input_is_documented(self):
        self.assertTrue(self.inputs)
        for name in sorted(self.inputs):
            with self.subTest(input=name):
                self.assertTrue(f"`{name}`" in self.readme,
                                f"{name} is a workflow input but absent from the README table")

    def test_the_table_invents_nothing(self):
        import re
        known = self.secrets | self.vars | {"GITHUB_TOKEN"}
        for name in sorted(set(re.findall(r"`([A-Z][A-Z_]{3,})`", self.section))):
            with self.subTest(named=name):
                self.assertTrue(name in known,
                                f"README names {name}, which team.yml never reads")

    def test_onboarding_points_at_the_table_rather_than_restating_it(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        onboarding = (root / "ONBOARDING.md").read_text()
        self.assertIn("Inputs and secrets", onboarding)


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


class SelfInstall(unittest.TestCase):
    """This repo consumes itself, and its stub is the ONE pin that must not move at release.

    ReleasePins flips together on a release commit that is tagged and deliberately not merged.
    `.github/workflows/claude.yml` lives on mainline permanently, so a `vN` written into it would
    be a fifth pin nothing asserts — and mainline would run its own team on assets from an older
    version of itself. A blanket mainline -> vN sweep across .github at release time is exactly
    the plausible edit this catches."""

    def test_the_self_install_tracks_mainline(self):
        import re
        ref = re.search(r"uses: matt-whitaker/claude-team/\.github/workflows/team\.yml@(\S+)", SELF).group(1)
        self.assertEqual(ref, "mainline")

    def test_the_inputs_are_filled_in(self):
        self.assertNotIn("CHANGE-ME", SELF)
        self.assertIn("project_owner: matt-whitaker", SELF)

    def test_the_permissions_ceiling_survives(self):
        # ⚠️ A called workflow cannot request permissions its caller did not grant. Trim any of
        # these and every run dies at startup, before a job exists to report it.
        for scope in ("contents: write", "issues: write", "pull-requests: write",
                      "actions: read", "id-token: write"):
            self.assertIn(scope, SELF, scope)

    def test_the_triggers_live_in_the_stub(self):
        # A called workflow's run-name is ignored and its workflow-level concurrency unsupported,
        # so both belong here rather than upstream.
        for key in ("on:", "issues:", "issue_comment:", "pull_request:", "run-name:", "concurrency:"):
            self.assertIn(key, SELF, key)

class CanonicalLabels(unittest.TestCase):
    """The label set is part of the consumer contract; the doc and the data must agree."""

    def setUp(self):
        import json
        root = pathlib.Path(__file__).resolve().parent.parent
        self.labels = json.load(open(root / "templates/labels.json"))
        self.onboarding = (root / "ONBOARDING.md").read_text()

    def test_every_label_has_a_colour_and_a_description(self):
        for l in self.labels:
            self.assertRegex(l["color"], r"^[0-9a-f]{6}$", l["name"])
            self.assertTrue(l["description"].strip(), f"{l['name']} has no description")

    def test_the_roles_the_workflow_stamps_all_have_labels(self):
        named = {l["name"] for l in self.labels}
        for role in ("architect", "implementor", "designer", "tester", "writer",
                     "researcher", "security", "complete"):
            self.assertIn(f"@claude/{role}", named)
        self.assertIn("@claude", named)

    def test_onboarding_points_at_the_file_rather_than_listing_them(self):
        self.assertIn("templates/labels.json", self.onboarding)

