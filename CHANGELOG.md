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

The upgrade procedure itself is [`INSTALL.md` §0](INSTALL.md).

---

## Unreleased

**Action required:** yes — App-driven repos set `CLAUDE_TEAM_DRIVER` to `cascade`; every consumer re-copies its `.claude/`, which now carries the session rule and skills as well.

- ⚠️ **claude-harness is folded into claude-team; the session half now ships from one repo.** The session rule moves in as `rules/claude-session.md` (its own `session-rule-revision`, independent of the workflow pin), beside the existing `rules/claude-team.md`. The `handoff` and `take-on-story` skills move in too, and a new `upgrade-team` skill carries the upgrade flow. On upgrade, a consumer re-copies `.claude/rules/*` and `.claude/skills/*` from this repo. `ONBOARDING.md` is renamed `INSTALL.md`. The session rule arrives at `session-rule-revision: 13`, continuing the sequence it carried as `harness-rule-revision` — revisions 1–12 and their entries live in the retired repo's history, and everything they shipped is already installed fleet-wide.
- ⚠️ **The default driver is now the SESSION; the App cascade is opt-in. App-driven repos must
  act.** A `driver` input decides who advances a story's waves. Its default — and the default of
  the repo variable `CLAUDE_TEAM_DRIVER` it is wired to — is **session-driven**: a human or a
  `take-on-story` session labels each wave, and **nothing auto-dispatches**. A repo that wants the
  App cascade sets `CLAUDE_TEAM_DRIVER` to `cascade` (Settings → Variables, no PR). **A repo that
  relied on the cascade and does nothing will go quiet** — its next task will not start itself.
  Set the variable to `cascade` to restore it. `allowed_bots` alone no longer turns the cascade
  on; the cascade needs both `driver: cascade` and a bot admitted. The safe default was the point:
  auto-dispatch starts runs unattended, so a misconfiguration now suppresses it rather than firing.

- **The cascade is one composite action, not three inline copies.** `dispatch-next` (mint token +
  run the hook) was copy-pasted into the delegate, architect and authors jobs; it is
  `.github/actions/dispatch-next` now, called at each site. Behavior is unchanged — same steps,
  same gates, same fail-open mint. The workflow core reads as event → route → run → check, with
  the cascade a single opt-in `uses:`, matching the two-driver model (a consumer with
  `allowed_bots` empty drives by session or hand; one that names a bot uses the cascade). No
  consumer action; a pinned consumer picks it up at its next bump.

- **The closed-trigger PR-opener verifies real parentage.** open-story-pr.py now checks the
  closed issue'''s actual parent matches the story its Branch line names, before opening a PR. The
  trigger is reachable by any issue author; the Branch line is attacker-controllable body text,
  the parent link is not. Ceiling was a premature PR, never code execution. No consumer action.
without it.

- **claude-team now ships law and procedure for consumers' `.claude/`.** `templates/settings/`
  is a settings fragment plus `guard-push.py` — harness-enforced: no default-branch push, no
  force-push, no `gh pr merge`, from any session in the repo. `skills/` ships `shape-story` and
  `diagnose-run`. Install is a verbatim copy (INSTALL §3); re-copying is the upgrade. A
  committed skill or hook is maintainer-owned law — reviewed merge is the governance, per the
  epic #78 drills.

- **A dark cascade no longer dispatches.** `allowed_bots: ""` now stops `dispatch-next.py`
  outright, whatever the App secrets say — previously a dark repo with secrets set dispatched a
  run that died at the actor guard after consuming the front-door label, blocking the real
  driver (#82). Consumers admitting a bot are unchanged.

- **A bare `@claude` comment no longer answers or routes — the CI root role bails.** It does its
  custodial work (repairs, stuck-task diagnosis) and otherwise replies that the fallback fired,
  pointing the maintainer to a session. Rule 1b's consult is removed with it: nothing turns a
  comment into a run any more except an explicit `@claude/<role>` handle. The label front door,
  the cascade, and `defaulted`-route interception are untouched. (Epic #78, the session-driver
  model.)

- **`hooks/run.py` is one entry point for the deterministic verbs** — `--list` names them, an
  unknown verb fails naming the known set, and a verb runs its hook with the caller's env and
  exit code. Adds no behaviour; it exists so a session driving a story invokes the same code a
  CI step does (epic #78, the verbs story). Nothing in `team.yml` changes.
- The install now asks the maintainer for the dispatch App's slug outright, beside the board,
  instead of deferring it to the App half of step 6. Prompted by an App rename: a stub admitting
  a stale slug refuses every cascaded run at setup, and the runbook now asks for the current
  name even when the installer thinks they know it.

## v2

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
- **⚠️ Your stub needs one more trigger type: `types: [labeled, closed]`.** Without it a task
  closed **by hand** still strands its story permanently — every other path to the story-PR hook is
  an event the machinery produces, so a human close reached "all tasks closed, branch ahead, no PR"
  with nothing able to resume it. `closed` is not a second front door: no run is routed from it, and
  a task closed by a hook fires nothing at all.
- **⚠️ A role step that succeeds but returns no handoff now FAILS the run.** It used to print
  *"no author ran, or its step failed"* — both halves false in that case — and report success while
  the task stayed open and the story halted. No action, but **expect a previously-green failure
  mode to start showing red**: that is the run telling you a task did not close. Re-trigger it.
  The transcript is also captured for that one case regardless of `AGENT_TRANSCRIPTS`, because why
  the step produced nothing is unknowable from anything else the run keeps.
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
