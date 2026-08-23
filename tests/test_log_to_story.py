import unittest
from harness import HookCase

# One story, one task per phase, deliberately created OUT of trigger order so the sort has
# something to do: the tester has the lowest number and must still come last.
STORY = {
    "600": {"kids": [
        {"number": 601, "title": "Cover it", "state": "open"},
        {"number": 602, "title": "Build it", "state": "open"},
        {"number": 603, "title": "Specify it", "state": "open"},
    ]},
    "601": {"body": "Branch: `600-thing`\nRole: tester"},
    "602": {"body": "Branch: `600-thing`\nRole: implementor"},
    "603": {"body": "Branch: `600-thing`\nRole: writer"},
}


class TheCaptionAgreesWithTheSort(HookCase):
    """⚠️ #30: THE CAPTION NAMED THE EXACT INVERSION THE SORT EXISTS TO PREVENT.

    `log-to-story.py` rendered "Order is derived — authors, then tests, then docs" under a table
    that `phase()` had correctly sorted writer-first. The two were independent statements of one
    fact and they drifted.

    ⚠️ It is worth more than its size because it is the sentence a reader trusts WHEN THE TABLE
    SURPRISES THEM. Seeing a writer task at the top, they look for the explanation — and found one
    confirming the wrong reading. A caption that disagrees with its own table is worse than none.

    The Writer runs first by design: a specification is only worth anything if it says what the
    code *should* do, which it cannot if written by reading the code that already exists."""

    def render(self):
        r = self.run_hook("log-to-story.py", {
            "STORY": "600", "GH_TOKEN": "ghs_fixturetoken", "STUB_ISSUES": STORY,
        })
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # ⚠️ `calls_matching` searches a call's ARGS, and the stub records the hook name as
        # `kind` — so matching on "upsert_comment" there silently finds nothing and every
        # assertion below passes vacuously. Filter on kind.
        posted = [c for c in r.calls if c["kind"] == "upsert_comment"]
        self.assertTrue(posted, f"the hook posted no comment; calls={r.calls}")
        return posted[0]["args"][1]

    def test_the_writer_sorts_first_despite_the_highest_number(self):
        body = self.render()
        order = [n for n in ("#603", "#602", "#601") if n in body]
        self.assertEqual(order, ["#603", "#602", "#601"], body)
        self.assertLess(body.index("#603"), body.index("#602"))
        self.assertLess(body.index("#602"), body.index("#601"))

    def test_the_caption_names_the_phases_in_the_order_the_table_uses(self):
        """The whole of #30. Read the caption's own sequence and check it against where the
        tasks actually landed — not against a literal string, which is what drifted."""
        body = self.render()
        caption = next(l for l in body.splitlines() if l.startswith("Order is derived"))
        named = caption.split("—", 1)[1].split(";")[0]
        # Assert presence before position — `str.index` on a missing word raises ValueError,
        # which reports a real defect as a test error rather than a failure.
        for word in ("writer", "authors", "tester"):
            self.assertIn(word, named, f"caption does not name every phase: {caption}")
        writer, authors, tester = (named.index(w) for w in ("writer", "authors", "tester"))
        self.assertLess(writer, authors, f"caption still puts the writer after the authors: {caption}")
        self.assertLess(authors, tester, f"caption still puts the tester before the authors: {caption}")

    def test_the_caption_does_not_say_docs_last(self):
        """The precise wording that shipped. Pinned so the exact regression cannot return."""
        body = self.render()
        self.assertNotIn("authors, then tests, then docs", body)

    def test_the_first_open_task_is_marked_ready_and_the_rest_wait(self):
        """Ready/waiting falls out of the same order, so a wrong sort would mis-mark them too."""
        body = self.render()
        ready = [l for l in body.splitlines() if "ready" in l]
        self.assertEqual(len(ready), 1, body)
        self.assertIn("#603", ready[0])


if __name__ == "__main__":
    unittest.main()
