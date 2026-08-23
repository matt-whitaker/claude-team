"""⚠️ THE LAYER SPLIT IS ONLY REAL IF SOMETHING CHECKS IT.

How a *session* works is `claude-harness`, installed here as `.claude/rules/claude-harness.md`.
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
RULE = ROOT / ".claude/rules/claude-harness.md"


class TheHarnessRuleIsInstalled(unittest.TestCase):
    def test_the_rule_is_present(self):
        self.assertTrue(RULE.exists(), f"{RULE} is missing — the harness is not installed here")

    def test_it_records_where_it_came_from_and_at_what_revision(self):
        """⚠️ Without the marker, "is this stale?" costs a full re-read of the file every time —
        the exact cost the install exists to remove. It is also what makes the upgrade a replace
        rather than a comparison."""
        text = RULE.read_text(encoding="utf-8")
        self.assertRegex(text, r"harness-rule-revision: \d+")
        self.assertIn("claude-harness", text)

    def test_it_is_replaced_not_merged(self):
        """⚠️ Nothing of this repo's may be written into it, or an upgrade clobbers repo content
        and the install goes back to being a merge — which is the thing the format removed."""
        text = RULE.read_text(encoding="utf-8")
        self.assertIn("replace it", text.lower())
        for local in ("mainline", "unittest", "board 9", "TEAM_REF"):
            with self.subTest(fact=local):
                self.assertNotIn(local, text,
                                 f"{local!r} is this repo's — it does not belong in a portable rule")


class TheLocalRuleCarriesOnlyThisRepo(unittest.TestCase):
    """⚠️ `working-here.md` is what is left after the portable half moved out. A fact that drifts
    back into it is invisible to every other repo that would hit the same trap — which is exactly
    what happened to four git lessons before the split.

    ⚠️ IT REPLACED `CLAUDE_CLOUD.md`, WHOSE CLOUD-NESS WAS AN ARTIFACT OF DELIVERY. That file
    existed because a cloud session has no memory and needed a committed one, so it carried a
    read-only-if-cloud gate, a never-`@path`-import warning, and a merge line dividing template
    framing from repo content. A rule is committed, loads in both environments, is discovered
    without being mentioned, and is owned by whoever ships it — so all three devices became
    unnecessary at once. `test_no_file_needs_a_gate_or_a_merge_line` pins that they stayed gone."""

    # ⚠️ READ IN setUp, NOT THE CLASS BODY — and this is the SECOND time in one session. A
    # class-body read of a missing file raises at IMPORT, which takes the whole module down and
    # turns every clean failure into one `unittest.loader._FailedTest`, hiding the rest. Caught
    # both times only by running the suite against the unfixed tree, which is the entire argument
    # for doing that before trusting a new test.
    def setUp(self):
        path = ROOT / ".claude/rules/working-here.md"
        self.assertTrue(path.exists(), f"{path} is missing")
        self.LOCAL = path.read_text(encoding="utf-8")

    def test_the_old_file_is_gone(self):
        self.assertFalse((ROOT / "CLAUDE_CLOUD.md").exists(),
                         "CLAUDE_CLOUD.md is superseded by .claude/rules/working-here.md")

    def test_no_file_needs_a_gate_or_a_merge_line(self):
        """The three workarounds the old shape required. Each returning would mean the content had
        drifted back into a file that has to be found, imported, or merged."""
        for device, phrase in (
            ("the read-only-if-cloud gate", "Read this only if you are"),
            ("the @path import warning", "unbackticked"),
            ("the repo-owned merge line", "REPO-OWNED BELOW THIS LINE"),
        ):
            with self.subTest(device=device):
                self.assertNotIn(phrase, self.LOCAL)

    def test_the_moved_facts_did_not_drift_back(self):
        moved = {
            "the ephemeral-container fact": "not committed and pushed is lost",
            "the push-into-tail trap": "exit status of",
            "the stale-ref trap": "stale info",
            "the checkout trap": "discards every uncommitted",
            "the prove-it-fails rule": "Prove a new test fails",
        }
        for name, phrase in moved.items():
            with self.subTest(fact=name):
                self.assertNotIn(phrase, self.LOCAL,
                                 f"{name} belongs in claude-harness, where every repo gets it")

    def test_it_still_carries_what_only_this_repo_knows(self):
        """The other direction. Stripping too much would send a session looking for facts that
        exist nowhere — the board number is the one with no other home."""
        for fact in ("board is 9", "workflow ON ITSELF", "Two pins move together"):
            with self.subTest(fact=fact):
                self.assertIn(fact, self.LOCAL)

    def test_it_says_where_the_portable_half_went(self):
        """A reader who remembers those facts being here must be told where they are now, or the
        move reads as a deletion."""
        self.assertIn("claude-harness", self.LOCAL)

    def test_both_rules_are_the_only_ones_installed(self):
        """⚠️ `ls .claude/rules/` is the manifest — that is the whole appeal of the format. A rule
        appearing without anyone deciding to add it is the manifest ceasing to mean anything."""
        found = sorted(p.name for p in (ROOT / ".claude/rules").glob("*.md"))
        self.assertEqual(found, ["claude-harness.md", "working-here.md"])


if __name__ == "__main__":
    unittest.main()
