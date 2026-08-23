import os
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


class TheConsumerNamesItsOwnToolchain(unittest.TestCase):
    """⚠️ #46: every authoring role was granted `Bash(npm|npx|node:*)` and nothing else, so an
    author in a Python-gated repo could not run the gate — including in THIS repo, whose gate is
    `python3 -m unittest`. Measured on run 32561656056: the Implementor reimplemented its
    assertion in `node` and reported that it had not run the Python suite. That is the ceiling of
    the constraint — a role producing a change it cannot verify.

    It also broke the package's own invariant: *nothing here names a consuming repo, its branches,
    its gate or its packages.* A toolchain is the same category as a gate."""

    # ⚠️ AN AUTHORING STEP IS ONE THAT CARRIES THE HANDOFF SCHEMA, not one whose tool string
    # happens to start `Edit,Write`. Matching on the shape of the string caught the ARCHITECT,
    # which holds `Read,Edit,Write` to rewrite an issue body and correctly has no runtime — it
    # writes no code and runs no gate. `--json-schema` is exactly the four roles that do.
    @staticmethod
    def _claude_args_blocks(text):
        """Each `claude_args: |` body, taken to the first line that dedents out of it.
        ⚠️ Deliberately NOT one regex: `\\s{12}` matches newlines, so a greedy version ran past
        the end of a step and swept the next role's flags into the same block."""
        blocks = []
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip() != "claude_args: |":
                continue
            body = []
            for nxt in lines[i + 1:]:
                if nxt.strip() and not nxt.startswith(" " * 12):
                    break
                body.append(nxt)
            blocks.append("\n".join(body))
        return blocks

    # ⚠️ AN AUTHORING ROLE IS ONE THAT RUNS IN THE `authors` JOB. Two narrower-looking
    # discriminators were tried and both were wrong: matching `Edit,Write` swept in the
    # ARCHITECT, which rewrites issue bodies and runs no gate; matching `--json-schema` swept in
    # the CUSTODIAN and the RESEARCHER, which also return JSON. The job boundary is the thing
    # that actually means "writes code, needs the consumer's gate".
    @staticmethod
    def _job(text, name):
        """One job's lines, from its key to the next key at the same indent.
        ⚠️ Line-walked rather than regexed — a lookahead for the NEXT job assumed a blank line
        before it and silently matched nothing when there wasn't one."""
        lines, out, inside = text.splitlines(), [], False
        for line in lines:
            if line == f"  {name}:":
                inside = True
                continue
            if inside and re.match(r"^  \S.*:$", line):
                break
            if inside:
                out.append(line)
        assert out, f"job {name} not found"
        return "\n".join(out)

    AUTHORS_JOB = _job.__func__(TEAM, "authors")

    AUTHOR_TOOLS = [
        re.search(r'--allowedTools "([^"]*)"', b).group(1)
        for b in _claude_args_blocks.__func__(AUTHORS_JOB)
        if "--allowedTools" in b
    ]

    def test_all_four_authoring_roles_are_found(self):
        """Guards the extraction above: if it stops matching, every assertion below passes
        vacuously — and a test that cannot fail is worse than no test."""
        self.assertEqual(len(self.AUTHOR_TOOLS), 4, self.AUTHOR_TOOLS)

    def test_the_architect_is_not_swept_in(self):
        """It rewrites issue bodies, so it holds `Read,Edit,Write` and looks like an author to
        anything matching on that. It runs no gate and must gain no runtime."""
        self.assertIn('--allowedTools "Read,Edit,Write,Bash(gh:*),Bash(git:*)"', TEAM)

    def test_no_author_allowlist_hard_codes_a_toolchain(self):
        for tools in self.AUTHOR_TOOLS:
            with self.subTest(tools=tools):
                for named in ("npm", "npx", "node", "python", "go:", "cargo", "bundle"):
                    self.assertNotIn(named, tools,
                                     f"{named} is a consumer's toolchain; it belongs in `runtimes`")

    def test_every_author_takes_the_resolved_grant(self):
        for tools in self.AUTHOR_TOOLS:
            with self.subTest(tools=tools):
                self.assertIn("${{ steps.runtimes.outputs.grants }}", tools)

    def test_the_authors_still_hold_git_and_gh_unconditionally(self):
        """`runtimes` widens the gate, it does not replace what an author has always needed:
        the landing hooks are not the only thing that touches git, and `gh` is how a role reads
        its own issue."""
        for tools in self.AUTHOR_TOOLS:
            with self.subTest(tools=tools):
                self.assertIn("Bash(git:*)", tools)
                self.assertIn("Bash(gh:*)", tools)

    def test_the_default_reproduces_the_old_fixed_list(self):
        """⚠️ A consumer upgrading past this change must see no behaviour difference. The old
        grant was npm, npx and node; the default has to be exactly that, or the release breaks
        every existing install."""
        self.assertRegex(TEAM, r'runtimes:\n\s+description:[\s\S]*?default: "npm,npx,node"')

    def test_the_stub_and_the_self_install_both_declare_it(self):
        self.assertIn("runtimes:", STUB)
        self.assertIn('runtimes: "python3"', SELF,
                      "this repo's gate is python3 — it is the case #46 was found on")

    def test_the_narrow_role_allowlists_are_untouched(self):
        """The Researcher holds no shell BY DESIGN, and the Custodian and Security are
        allowlisted by subcommand. `runtimes` is for the authoring roles only — widening any of
        these three would undo a deliberate bound."""
        self.assertIn('--allowedTools "Read,WebSearch,WebFetch"', TEAM)
        for narrow in ("Bash(gh issue view:*)", "Bash(gh pr diff:*)"):
            self.assertIn(narrow, TEAM)
        self.assertNotIn('Read,WebSearch,WebFetch${{', TEAM)


class TheRuntimesResolverActuallyRuns(unittest.TestCase):
    """⚠️ PINNING THE YAML PROVES THE WIRING, NOT THE BEHAVIOUR. The resolver is a shell script
    that sanitises consumer-supplied text before it lands inside a quoted `--allowedTools` string
    the action parses line by line. A bad entry must fail the step, not silently rewrite the flags
    after it — so the script itself is extracted and executed here."""

    def script(self):
        """The `run:` body of the `id: runtimes` step, dedented."""
        block = re.search(
            r"- id: runtimes\n(?:.*\n)*?        run: \|\n((?:          .*\n|\n)+)", TEAM)
        self.assertIsNotNone(block, "could not find the runtimes step's run: body")
        return "".join(l[10:] if l.startswith(" " * 10) else l
                       for l in block.group(1).splitlines(keepends=True))

    def resolve(self, value):
        import subprocess
        return subprocess.run(
            ["bash", "-c", self.script()],
            capture_output=True, text=True,
            env={**os.environ, "RUNTIMES": value, "GITHUB_OUTPUT": self.out},
        )

    def setUp(self):
        import tempfile
        fd, self.out = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(os.unlink, self.out)

    def grants(self, value):
        r = self.resolve(value)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        written = open(self.out).read()
        return dict(l.split("=", 1) for l in written.splitlines() if "=" in l)["grants"]

    def test_the_default_expands_to_the_old_fixed_list(self):
        self.assertEqual(self.grants("npm,npx,node"),
                         ",Bash(npm:*),Bash(npx:*),Bash(node:*)")

    def test_a_single_runtime_works(self):
        self.assertEqual(self.grants("python3"), ",Bash(python3:*)")

    def test_surrounding_whitespace_is_tolerated(self):
        self.assertEqual(self.grants(" python3 , go "), ",Bash(python3:*),Bash(go:*)")

    def test_an_empty_entry_is_skipped_rather_than_expanded(self):
        self.assertEqual(self.grants("python3,,go"), ",Bash(python3:*),Bash(go:*)")

    def test_an_entry_that_could_rewrite_the_flags_fails_the_step(self):
        """The value sits inside `--allowedTools "…"`. A quote, or anything that reaches the
        parser as a new argument, could widen the grant far past what the consumer wrote."""
        for hostile in ['node:*)",Bash', "node'", 'node"', "node;rm -rf /", "Bash(node:*)"]:
            with self.subTest(entry=hostile):
                r = self.resolve(hostile)
                self.assertNotEqual(r.returncode, 0, f"{hostile!r} was accepted")
                self.assertIn("::error::", r.stdout + r.stderr)

    def test_resolving_to_nothing_fails_rather_than_granting_nothing(self):
        """⚠️ An author with no runtime cannot run any gate. Failing loudly beats a run that
        silently cannot verify anything — that silence is the whole of #46."""
        for empty in ("", "  ", ",,,"):
            with self.subTest(value=repr(empty)):
                r = self.resolve(empty)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("::error::", r.stdout + r.stderr)


class TheReturningConsumerHasAPath(unittest.TestCase):
    """⚠️ #39: ONBOARDING INSTALLED AND NEVER RE-INSTALLED. Every step was written for a fresh
    target — §2 creates the stub, §3 creates overlays, §7 is a first-run drill — so a session
    pointed at an installed repo had no instruction for the case it was actually in, and the
    consumer half of an upgrade was never stated anywhere. "Upgrade" meant bump the ref and hope.

    ⚠️ The version signal already existed: the `vN` tags and the `@ref` in every consumer's stub.
    What was missing is what a bump *requires*, and what a bump can never carry."""

    ROOT = pathlib.Path(__file__).resolve().parent.parent

    # ⚠️ READ IN setUp, NOT THE CLASS BODY. The other classes here read at module scope, which is
    # fine for files that have always existed — but a class-body read of a file this change is
    # INTRODUCING raises at import time, which takes the whole module down and hides every
    # unrelated test in it. Caught by running these against mainline: the intended assertion
    # failure arrived as `unittest.loader._FailedTest` with 40-odd other tests silently gone.
    def setUp(self):
        missing = [f for f in ("ONBOARDING.md", "CHANGELOG.md", "CLAUDE.md")
                   if not (self.ROOT / f).exists()]
        self.assertFalse(missing, f"required file(s) absent: {missing}")
        self.ONBOARDING = (self.ROOT / "ONBOARDING.md").read_text()
        self.CHANGELOG = (self.ROOT / "CHANGELOG.md").read_text()
        self.CLAUDEMD = (self.ROOT / "CLAUDE.md").read_text()

    def test_the_upgrade_path_comes_before_the_install_steps(self):
        """⚠️ A returning reader must not have to read §1-§7 to discover they are in the wrong
        place — §3 would overwrite an overlay carrying the repo's whole personality."""
        upgrade = self.ONBOARDING.index("## 0. Already installed?")
        first_install_step = self.ONBOARDING.index("## 1. Decide the four inputs")
        self.assertLess(upgrade, first_install_step)

    def test_the_install_steps_are_signposted_as_not_for_a_returning_reader(self):
        self.assertRegex(self.ONBOARDING, r"ALREADY INSTALLED.*§0")

    def test_the_case_is_detected_from_the_pin_not_a_new_number(self):
        """⚠️ Copying claude-code's revision integer would be wrong: it needed one because its
        install target is a session's knowledge and nothing else numbered it. Here the pin already
        is the version, and a second number beside it invents a fact that exists."""
        self.assertIn("the pin *is* the signal", self.ONBOARDING)
        self.assertIn("git ls-remote --tags", self.ONBOARDING)

    def test_the_consumer_is_never_told_to_edit_TEAM_REF(self):
        """It lives inside the workflow and moves with the tag. A consumer holds exactly one pin."""
        section = self.ONBOARDING[
            self.ONBOARDING.index("## 0."):self.ONBOARDING.index("## 1.")]
        self.assertIn("only pin a consumer holds", section)

    def test_the_pin_cannot_carry_labels_and_the_path_says_so(self):
        """⚠️ THE HALF NO VERSION NUMBER REACHES. Labels live in GitHub, not the clone, so no ref
        bump has ever touched them — and the one step already written to be idempotent is the one
        that drifted, because nothing told anyone to re-run it."""
        section = self.ONBOARDING[
            self.ONBOARDING.index("## 0."):self.ONBOARDING.index("## 1.")]
        self.assertIn("unconditionally", section)
        for carried in ("label", "board", "settings"):
            with self.subTest(item=carried):
                self.assertIn(carried, section.lower())

    def test_the_overlay_wins_over_a_tightened_base_rule(self):
        """⚠️ Measured, not hypothetical: the Writer's scope was narrowed in the base and two
        consumer overlays went on granting what had just been removed."""
        section = self.ONBOARDING[
            self.ONBOARDING.index("## 0."):self.ONBOARDING.index("## 1.")]
        self.assertIn("composes *after* the base", section)

    def test_every_changelog_version_states_whether_to_act(self):
        """⚠️ THE ONLY QUESTION A CONSUMER HAS. A list of merged PRs cannot answer it, so the
        marker is asserted rather than trusted to habit — `no` is the commonest answer and the
        most valuable one."""
        headings = [m for m in re.finditer(r"^## (.+)$", self.CHANGELOG, re.M)]
        self.assertTrue(headings, "the changelog has no version headings")
        for i, head in enumerate(headings):
            end = headings[i + 1].start() if i + 1 < len(headings) else len(self.CHANGELOG)
            body = self.CHANGELOG[head.end():end]
            with self.subTest(version=head.group(1)):
                self.assertRegex(
                    body, r"\*\*Action required:\*\* (yes|no|n/a|unknown)",
                    f"{head.group(1)} does not say whether a consumer must act")

    def test_there_is_always_somewhere_to_write_the_next_entry(self):
        """⚠️ The entry is written in the PR that CAUSES it. Reconstructing consumer impact from a
        merge log is the work this file exists to remove, and it is done worst by whoever is trying
        to cut a tag."""
        self.assertIn("## Unreleased", self.CHANGELOG)

    def test_the_changelog_says_what_it_is_not(self):
        self.assertIn("not a merge log", self.CHANGELOG)

    def test_the_release_procedure_renames_the_unreleased_heading(self):
        """⚠️ A changelog nobody is told to roll over accumulates one permanent Unreleased section
        and stops distinguishing versions — which is the whole mechanism §0 reads."""
        release = self.CLAUDEMD[self.CLAUDEMD.index("**Releasing**"):][:600]
        self.assertIn("Unreleased", release)
        self.assertIn("CHANGELOG.md", release)


class TheEmptyHandoffKeepsItsEvidence(unittest.TestCase):
    """⚠️ #32, second half. A role step that succeeds and returns no handoff silently halts a
    story, and WHY it produced nothing is unknowable from anything else the run keeps. On the run
    that produced the issue, `AGENT_TRANSCRIPTS` was unset — so the channel-with-no-reader failure
    landed on exactly the run that needed it."""

    def test_the_handoff_step_is_addressable(self):
        """Guards the two assertions below: without the id, `steps.handoff.outputs` resolves to
        nothing and the override silently never fires."""
        self.assertIn("id: handoff", TEAM)

    def test_a_successful_step_with_no_handoff_overrides_the_toggle(self):
        self.assertIn("steps.handoff.outputs.evidence == 'true'", TEAM)

    def test_the_toggle_still_governs_every_other_case(self):
        """The override is an OR, not a replacement — an ordinary run stays inert until someone
        opts in, which is what keeps transcripts off a public console by default."""
        self.assertIn("contains(vars.AGENT_TRANSCRIPTS, 'authors')", TEAM)

    def test_all_four_author_outcomes_reach_the_hook(self):
        """⚠️ Pairs, not a `||` chain. A skipped step's outcome is the truthy string "skipped",
        so the chain used for `structured_output` would always take the first and name the wrong
        step's fate — which is the misreport this whole issue is about."""
        for role in ("implementor", "designer", "tester", "writer"):
            with self.subTest(role=role):
                self.assertIn(f"{role}=${{{{ steps.{role}.outcome }}}}", TEAM)


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

