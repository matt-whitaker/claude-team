# CHANGELOG — what a consumer has to do

⚠️ **This is not a merge log, and turning it into one destroys its only purpose.** A consumer
reading it has exactly one question — *do I have to do something?* — and a list of PR titles
cannot answer it. Entries name **consumer-side consequences**, or say plainly that there are none.

⚠️ **Every version heading carries an `**Action required:**` line, and a test asserts it.** `no` is
the commonest and most valuable answer: a release nobody has to act on should say so in one word
rather than leaving a reader to diff the tag themselves.

⚠️ **Write the entry in the PR that causes it, not at release time.** Reconstructing consumer
impact from a merge log is exactly the work this file exists to remove, and it is done worst by
whoever is trying to cut a tag. `## Unreleased` is always open for that reason.

The upgrade procedure itself is [`ONBOARDING.md` §0](ONBOARDING.md).

---

## Unreleased

**Action required:** yes — one stub input, one label re-sync, one overlay check.

- **The stub gains a `runtimes` input.** It names the commands an authoring role may run, so it
  can execute *your* gate. It defaults to `npm,npx,node` — exactly the fixed grant every consumer
  had before — so **an unchanged stub keeps working**. Set it if your gate is not npm-driven
  (`python3`, `go`, `cargo`, `bundle`). Until you do, an author in such a repo produces changes it
  cannot verify and says so in a report section that is easy to miss.
- **⚠️ Re-run the label loop (§4).** `story`, `task` and `spike` changed colour so no
  classification label shares one with a routing label. A pin bump cannot carry this — labels live
  in GitHub, not in the clone.
- **⚠️ Check your Writer overlay.** The base prompt no longer gives any role ownership of
  `CLAUDE.md`, `AGENTS.md`, `.claude/**` or `.claude-team/**`. An overlay composes *after* the
  base, so an overlay that still grants them **wins over this change** and nothing here can reach
  it. Two known cases in the fleet at the time of writing.
- **The Architect prompt now names the as-is story** — a story left whole, carrying its own
  `Branch:` line and a `Role:` stamp. No consumer action; it is the shaping side of a path routing
  already supported. Expect fewer unnecessary Writer tasks on small stories.
- **⚠️ Three base author prompts stopped contradicting the shared rule.** `implementor.md`,
  `designer.md` and `tester.md` still described the removed per-task-PR model — *"cut your own
  branch off the story's, and open your own PR into it"* — against `_shared.md`'s *"A TASK HAS NO
  PR"*, inside the same composed prompt. **Check your overlays for the same wording**: an overlay
  composes after the base and wins, so a role section restating the old model there is untouched by
  this fix.
- **The story task-order comment's caption was wrong** — it read *"authors, then tests, then
  docs"* under a table correctly sorted writer-first. No action; the sort itself was never wrong,
  only the sentence explaining it.
- **Story PRs and landings report their failures.** `open-story-pr.py` now says what `gh` refused
  and names the two usual causes; `finish-pr.py` no longer reports landed work as stranded. No
  action — but if you have been opening story PRs by hand, the next failure will tell you why.

## v1.1

**Action required:** unknown — this file did not exist yet.

Not reconstructed. 24 commits separate `v1.1` from the entry above, and inferring consumer impact
from them after the fact is guesswork of exactly the kind this file replaces. A consumer upgrading
across this boundary should follow §0 in full rather than trust a summary written backwards.

## v1

**Action required:** n/a — the first release.
