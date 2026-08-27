"""⚠️ THE LAYER SPLIT IS ONLY REAL IF SOMETHING CHECKS IT.

How a *session* works is `rules/claude-session.md`, installed here as
`.claude/rules/claude-session.md` like any other consumer.
How the *GitHub agents* work is this repo. One question sorts them — who invoked it — and the
whole point of separating them is that "does this serve a purpose?" becomes answerable, because a
file can no longer be serving the other layer.

⚠️ Crossing that line has already cost defects here, and BOTH OF THEM WORKED, which is why they
survived: the Architect reached the as-is story by citing this repo's own `CLAUDE.md` (#47), and
every author's toolchain was hard-coded into a package whose stated invariant forbids naming one
(#46). A crossed boundary does not announce itself — it produces right behaviour for the wrong
reason and holds until the reason stops being true. Hence a test rather than a convention.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULE = ROOT / ".claude/rules/claude-session.md"


class TheSessionRuleIsInstalled(unittest.TestCase):
    def test_the_rule_is_present(self):
        self.assertTrue(RULE.exists(), f"{RULE} is missing — the session rule is not installed here")

    def test_it_records_where_it_came_from_and_at_what_revision(self):
        """⚠️ Without the marker, "is this stale?" costs a full re-read of the file every time —
        the exact cost the install exists to remove. It is also what makes the upgrade a replace
        rather than a comparison."""
        text = RULE.read_text(encoding="utf-8")
        self.assertRegex(text, r"session-rule-revision: \d+")
        self.assertIn("claude-session", text)

    def test_it_is_replaced_not_merged(self):
        """⚠️ Nothing of this repo's may be written into it, or an upgrade clobbers repo content
        and the install goes back to being a merge — which is the thing the format removed."""
        text = RULE.read_text(encoding="utf-8")
        self.assertIn("replace it", text.lower())
        for local in ("mainline", "unittest", "board 9", "TEAM_REF"):
            with self.subTest(fact=local):
                self.assertNotIn(local, text,
                                 f"{local!r} is this repo's — it does not belong in a portable rule")


class RulesHoldInstalledModulesOnly(unittest.TestCase):
    """⚠️ `ls .claude/rules/` is the manifest of what is installed here, which only means anything
    while every entry came from somewhere else. A file the repo wrote itself sitting in that
    directory makes the listing a mix of two things and the manifest stops answering the question.

    ⚠️ No install writes a `CLAUDE.md`, which is what makes the division checkable rather than a
    matter of taste: a file that arrived from an install is a rule, a file nobody installed is
    `CLAUDE.md`."""

    RULES = ROOT / ".claude/rules"

    def test_every_installed_rule_names_where_it_came_from(self):
        for rule in sorted(self.RULES.glob("*.md")):
            with self.subTest(rule=rule.name):
                text = rule.read_text(encoding="utf-8")
                self.assertRegex(
                    text, r"-revision: \d+",
                    f"{rule.name} carries no revision — an install compares one, so a file "
                    "without one was not installed and does not belong here")

    def test_the_manifest_is_the_modules_and_nothing_else(self):
        found = sorted(p.name for p in self.RULES.glob("*.md"))
        self.assertEqual(found, ["claude-session.md"])

    def test_this_repos_own_facts_live_in_claude_md(self):
        """The content that used to sit beside the module. It has one home, and a session reading
        `CLAUDE.md` must find it there."""
        text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        for fact in ("Board: **9**", "RUNS THE TEAM WORKFLOW ON ITSELF",
                     "no single quote", "need a LOCAL session"):
            with self.subTest(fact=fact):
                self.assertIn(fact, text)

    def test_the_old_files_are_gone(self):
        for stale in ("CLAUDE_CLOUD.md", ".claude/rules/working-here.md"):
            with self.subTest(path=stale):
                self.assertFalse((ROOT / stale).exists())


if __name__ == "__main__":
    unittest.main()
