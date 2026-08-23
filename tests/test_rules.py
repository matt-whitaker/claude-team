"""The rule set is only useful if a citation can be trusted.

`RULES.md` names the rules that `CLAUDE.md`'s ⚠️ paragraphs are instances of, and a paragraph
cites one by opening with its id — `⚠️ [E4] **...**`. Tagging is opportunistic, so an *untagged*
paragraph is not a defect and nothing here counts them.

What is checkable without knowing which paragraph should carry which id: that every id cited
anywhere resolves to a rule that exists, that the ids are unique and unbroken, and that every
engine rule carries the measured evidence W1 says it must. A citation naming a rule that was
renamed or never existed is worse than no citation — it reads as grounding and is not.
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = (ROOT / "RULES.md").read_text(encoding="utf-8")
CLAUDE = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

# A rule is defined by its own heading: "### E4 — ..." or "### W1 — ..."
DEFINED = re.findall(r"^### ([EW]\d+) — ", RULES, re.MULTILINE)
# A citation is the id in brackets, anywhere: "⚠️ [E4] **...**"
CITED = set(re.findall(r"\[([EW]\d+)\]", CLAUDE)) | set(re.findall(r"\[([EW]\d+)\]", RULES))


class RuleIds(unittest.TestCase):
    def test_rules_are_defined(self):
        self.assertTrue(DEFINED, "RULES.md defines no rules; the heading form is '### E1 — ...'")

    def test_ids_are_unique(self):
        dupes = {i for i in DEFINED if DEFINED.count(i) > 1}
        self.assertFalse(dupes, f"duplicate rule ids: {sorted(dupes)}")

    def test_each_family_is_numbered_without_gaps(self):
        """A gap means a rule was deleted rather than superseded in place.

        W3 is explicit that a rule which turns out to be wrong stays, with a note saying what was
        tried and why it failed. Renumbering breaks every citation that already pointed at it, and
        deleting removes the reason nobody should try it again — so a hole in the sequence is the
        fingerprint of the one edit this file forbids.
        """
        for prefix in ("E", "W"):
            nums = sorted(int(i[1:]) for i in DEFINED if i.startswith(prefix))
            if not nums:
                continue
            self.assertEqual(
                nums, list(range(1, len(nums) + 1)),
                f"{prefix} ids must run 1..n with no gaps; found {nums}. "
                "Supersede a wrong rule in place rather than removing it.")

    def test_every_citation_resolves(self):
        """The whole point of an id is that it can be followed."""
        unknown = CITED - set(DEFINED)
        self.assertFalse(
            unknown,
            f"cited but not defined in RULES.md: {sorted(unknown)}. "
            "A citation that resolves to nothing reads as grounding and is not.")

    def test_every_engine_rule_carries_evidence(self):
        """W1: a rule earns its place by a measured failure, not by taste.

        The W rules are conventions about form and carry no run numbers, so they are exempt.
        An engine rule without an evidence line is a preference wearing the marker's clothes.
        """
        sections = re.split(r"^### ", RULES, flags=re.MULTILINE)[1:]
        missing = [
            s.split(" — ")[0] for s in sections
            if s.startswith("E") and "> Evidence:" not in s
        ]
        self.assertFalse(missing, f"engine rules with no evidence line: {missing}")


class RulesAreReachable(unittest.TestCase):
    def test_claude_md_points_at_the_rule_set(self):
        """A rule set nobody is sent to is E4's own failure, one level up.

        `CLAUDE.md` is the front door; a reader who never learns RULES.md exists will keep deriving
        rules from the record, which is the cost this file was written to stop.
        """
        self.assertIn("RULES.md", CLAUDE,
                      "CLAUDE.md must point at RULES.md, or the rule set has no reader")

    def test_the_citation_form_is_documented(self):
        self.assertIn("⚠️ [E4] **", RULES,
                      "RULES.md must show the citation form it expects paragraphs to use")
