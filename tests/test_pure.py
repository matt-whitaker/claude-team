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


class SequencingRefs(unittest.TestCase):
    def test_no_section_is_none_not_empty(self):
        self.assertIsNone(team.sequencing_refs("plain body"))

    def test_a_section_naming_nothing_is_empty_not_none(self):
        self.assertEqual(team.sequencing_refs("### Sequencing\n\nwriter, then tester.\n"), [])

    def test_numbered_lines_become_waves(self):
        self.assertEqual(
            team.sequencing_refs("### Sequencing\n1. #11\n2. #12, #13\n"), [[11], [12, 13]])

    def test_refs_on_the_heading_line_are_unreachable(self):
        self.assertEqual(team.sequencing_refs("**Sequencing.** In order: #606, then #607."), [])

    def test_it_stops_at_the_next_heading(self):
        body = "### Sequencing\n1. #11\n\n## Out of scope\n2. #999\n"
        self.assertEqual(team.sequencing_refs(body), [[11]])


class ArchitectPromptExamplesParse(unittest.TestCase):
    """⚠️ THE PROMPT'S OWN EXAMPLE WAS THE ROOT CAUSE OF #28.

    `**Sequencing.** Its tasks run in order: #606, then #607, then #608.` shipped as a worked
    example, matched the heading, and parsed to zero waves — so an Architect following the prompt
    exactly produced an inert section. A prompt that demonstrates a form the reader cannot parse
    is worse than one that says nothing, and prose alone could never have caught it.
    """

    def setUp(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        self.prompt = (root / "prompts/architect.md").read_text()

    def examples(self):
        import re
        blocks = re.findall(r"```\n(.*?)```", self.prompt, re.S)
        return [b for b in blocks if re.search(r"(?i)sequencing", b)]

    def test_every_story_form_example_parses_to_at_least_one_wave(self):
        """The `### Sequencing` block form, which `dispatch-next.py` reads."""
        story_form = [b for b in self.examples() if b.lstrip().startswith("### Sequencing")]
        self.assertTrue(story_form, "no story-form Sequencing example in the Architect prompt")
        for block in story_form:
            with self.subTest(block=block.strip()[:60]):
                self.assertTrue(
                    team.sequencing_refs(block),
                    "this example parses to nothing a hook can act on")

    def test_the_epic_form_is_prose_and_that_is_correct(self):
        """⚠️ TWO FORMS, TWO PARSERS, AND ONE OF THEM LOOKS LIKE THE TRAP.

        An epic's section is read by `file-sub-issues.py`, which takes any `#N` on any line —
        so the inline `**Sequencing.**` prose form is legitimate there. The identical form on a
        STORY is the #28 defect, because `dispatch-next.py` only reads refs from lines starting
        with a number. Pinned so nobody 'fixes' the epic example to match the story one, or the
        reverse.
        """
        import re
        epic_form = [b for b in self.examples() if b.lstrip().startswith("**Sequencing.**")]
        self.assertTrue(epic_form, "no epic-form Sequencing example in the Architect prompt")
        for block in epic_form:
            with self.subTest(block=block.strip()[:60]):
                self.assertEqual(team.sequencing_refs(block), [],
                                 "epic form is prose — inert to the story parser by design")
                self.assertTrue(re.findall(r"#(\d+)", block),
                                "an epic's section still has to name its stories")

    def test_the_prose_form_is_named_as_forbidden(self):
        self.assertIn("NEVER AS PROSE", self.prompt)


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


class TheArchitectPromptNamesTheAsIsStory(unittest.TestCase):
    """⚠️ #47: THE PROMPT DESCRIBED TWO OF THE THREE SHAPES A STORY CAN END IN.

    `delegate.py` routes three ways — a story WITH tasks dispatches its first wave, a story with
    no tasks falls through to its stamped author (the as-is path), and one with neither stamp nor
    tasks defaults to the Implementor and announces the guess. The prompt described the first,
    was silent on the second, and carried two absolute rules that could not both hold on a small
    story: *don't split what one author can finish* against *a Writer task on EVERY story,
    always*. A Writer task is a task, so obeying the second made the first unreachable.

    The Architect got it right on #43 anyway — by citing **CLAUDE.md**, which is this repo's own
    file and says nothing of the sort in a consumer. Prose review passed the contradiction, so it
    is pinned here instead."""

    def setUp(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        self.prompt = (root / "prompts/architect.md").read_text()

    def test_the_as_is_story_is_named_as_an_outcome(self):
        self.assertIn("AS-IS STORY", self.prompt)

    def test_the_story_level_role_stamp_is_shown(self):
        """The stamp is what routing reads. Without it the router guesses and says so on the
        issue at every trigger — so the prompt has to show the line, not just mention it."""
        self.assertRegex(
            self.prompt,
            r"\*\*Role: <implementor\|designer\|tester\|writer>\*\*",
            "the as-is story's Role line is not shown as a literal the Architect can copy")

    def test_the_writer_rule_is_scoped_rather_than_unconditional(self):
        """⚠️ BOTH DIRECTIONS MATTER. Unscoped, it contradicts 'do not split a one-author
        story'. Softened to a judgement, it reverts to the failure that produced it — asked to
        predict whether documentation was needed, the Architect answered no on every story ever
        shaped. So: scoped to stories that divide, and still not a judgement inside that scope."""
        self.assertNotIn("task on EVERY story", self.prompt)
        self.assertIn("every story you cut into tasks", self.prompt)
        self.assertRegex(
            self.prompt, r"not a judgement\s+call once the story divides",
            "the Writer rule is unscoped again — it contradicts step 4 that way")

    def test_the_reason_the_rule_exists_survives_the_rescoping(self):
        """A rule with its history removed is the one a later edit softens away."""
        self.assertIn("not one Writer task was ever cut", self.prompt)

    def test_the_discriminator_is_stated_rather_than_left_to_feel(self):
        self.assertIn("whether a specification needs writing before the code", self.prompt)

    def test_ambiguity_resolves_towards_dividing(self):
        self.assertIn("In doubt, divide", self.prompt)


if __name__ == "__main__":
    unittest.main()
