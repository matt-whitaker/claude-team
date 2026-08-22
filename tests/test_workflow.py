import pathlib
import re
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


class NoHookReadsAChannelNobodyFills(unittest.TestCase):
    """⚠️ THE DEAD CHANNEL IS THIS PACKAGE'S MOST-REPEATED DEFECT — `DEFAULTED`, the author
    handoff, `decisions` on the PR path, `docsCandidates`, `unrepairable`, and #44: a signal
    produced, consumed by nobody, and believed to work because nothing fails when it is absent.

    `finish-pr.py` is the sixth. `work-completion.py` had emitted `landed_ref` for as long as it
    had existed and the workflow read it at ONE of its two readers, so the hook that needed it to
    tell a landing from a loss saw an empty string forever — announced landed work as stranded,
    pushed the runner's throwaway branch, and named a ref that dies with the container as where
    the commits were safe.

    ⚠️ This asserts the WIRING, not the value: a var read by a hook and set nowhere in the
    workflow can only ever be empty. It cannot check that the right STEP sets it — several hooks
    take different vars per mode, and demanding all of them at every site would be false — so a
    per-hook test still has to cover which site."""

    HOOKS = pathlib.Path(__file__).resolve().parent.parent / "hooks"
    # Actions sets these itself, and the test harness sets the last two.
    AMBIENT = {"GITHUB_OUTPUT", "RUNNER_TEMP", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT",
               "GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "HOOKS_DIR", "CALLS_FILE"}

    def test_every_env_var_a_hook_reads_is_set_somewhere(self):
        for hook in sorted(self.HOOKS.glob("*.py")):
            src = hook.read_text()
            reads = set(re.findall(
                r"os\.environ(?:\.get)?[\(\[]\s*\"([A-Z][A-Z0-9_]*)\"", src))
            for name in sorted(reads - self.AMBIENT):
                with self.subTest(hook=hook.name, var=name):
                    # `NAME:` in an env block, or `NAME=` inline on a run line.
                    self.assertRegex(
                        TEAM, rf"(^|[\s;]){name}[:=]",
                        f"{hook.name} reads {name}; team.yml never sets it, so it is always empty",
                    )

    def test_finish_pr_is_told_what_the_landing_landed(self):
        """The specific wiring #44 was missing — the hook cannot distinguish a landed run from
        a stranded one without it, and both look identical from `origin/<default>..HEAD`."""
        self.assertIn("LANDED_REF: ${{ steps.completion.outputs.landed_ref }}", TEAM)


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

    def test_no_description_exceeds_githubs_limit(self):
        """⚠️ GitHub caps a label description at 100 characters, and `gh label create` FAILS over
        it — so an over-long description does not degrade, it breaks the install loop partway
        through and leaves the set half-applied."""
        for l in self.labels:
            with self.subTest(label=l["name"]):
                self.assertLessEqual(
                    len(l["description"]), 100,
                    f"{l['name']} is {len(l['description'])} chars; gh will reject it")

    def test_no_two_labels_share_a_colour_unless_the_pairing_is_deliberate(self):
        """⚠️ THE COLOUR IS THE ONLY THING A BOARD SHOWS AT A GLANCE, and this set carries two
        kinds of label for two different readers: ROUTING says what should happen to an issue and
        is the maintainer's, CLASSIFICATION says what an issue is and anyone filing may apply it.
        `story` shipped in the tester's green and `task`/`spike` in the authors' blue, so the
        board erased that line exactly where CLAUDE.md draws it in prose.

        Three pairings are deliberate — shaping, authoring, done — and they are enumerated here
        rather than derived, so a fourth is an edit someone has to argue for. The assertion runs
        both ways: nothing else may collide, and these three may not be silently split.

        ⚠️ Pinned as the GENERAL rule rather than as the three collisions that were found. The
        next colour edit will be somewhere else in the set, and a test naming only today's
        offenders would pass through the same mistake made one label over."""
        deliberate = {
            frozenset({"@claude/architect", "@claude/researcher"}),
            frozenset({"@claude/implementor", "@claude/designer"}),
            frozenset({"@claude/tester", "@claude/complete"}),
        }
        groups = {}
        for l in self.labels:
            groups.setdefault(l["color"], set()).add(l["name"])
        for color, names in sorted(groups.items()):
            with self.subTest(color=color):
                if len(names) > 1:
                    self.assertIn(
                        frozenset(names), deliberate,
                        f"{sorted(names)} all share #{color}; only the role pairings may")
        by_name = {l["name"]: l["color"] for l in self.labels}
        for pair in deliberate:
            a, b = sorted(pair)
            with self.subTest(pairing=(a, b)):
                self.assertEqual(by_name[a], by_name[b],
                                 f"{a} and {b} are a deliberate pairing and must stay one colour")

    def test_the_task_description_does_not_claim_a_task_owns_a_pr(self):
        """⚠️ IT SHIPPED SAYING THE OPPOSITE OF THE HIERARCHY: "A slice of a story, with its own
        branch and PR" — a fossil of the version before task PRs were removed.

        The PR is owned at the STORY level, which includes an unparented task or a bug;
        `CLAUDE.md:215` is the mechanism — when `story_from_branch(named) == ISSUE` the executing
        issue owns the branch and carries the PR, when they differ it is a task and it does not.

        A label description is read exactly when someone is unsure what the kind means, so it is
        wrong at the only moment it matters — and this file is the canon every consumer applies,
        so the error ships rather than staying local.
        """
        import re
        desc = next(l["description"] for l in self.labels if l["name"] == "task")
        self.assertIn("story's branch", desc,
                      "the task description must say where its commits actually land")
        self.assertIsNone(
            re.search(r"(?i)\bits own\b[^.]*\bPR\b", desc),
            "the task description claims a task has its own PR; the story level owns it")

