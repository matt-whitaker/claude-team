# The engine rules

`CLAUDE.md` records what went wrong and what was done about it. This file names the rules those
records are instances of, so the next one can cite a rule instead of deriving it again.

**Why this exists.** The record counts its own repetitions — *"the fifth instance of this exact
shape"*, *"the sixth dead channel"*, *"this trap survived being documented and was written again
anyway, twice"*. A rule discovered six times is a rule that was never named. Naming it is the
cheapest thing that stops a seventh.

**How to use it.**

- A ⚠️ paragraph in `CLAUDE.md` may open with its rule id — `⚠️ [E4] **…**` — naming the rule the
  failure is an instance of. Tag as you go: a paragraph picks up its id when someone next edits it.
  There is no sweep, and an untagged paragraph is not a defect.
- A **new** ⚠️ paragraph should cite a rule or say plainly that it is a new one. If it is new, add
  it here in the same commit.
- Citing an id that does not exist here fails the suite (`RuleIds` in `tests/test_rules.py`).
- These ids are stable. A rule that turns out to be wrong is **superseded in place**, with a note
  saying what was tried and why it failed — never renumbered, never deleted. See W3.

**What is not here.** Settled design decisions of this engine — one story, one branch, one PR; the
Writer runs first; tasks share the story's branch — are mechanism, not axioms. They live in
`CLAUDE.md`. So do platform facts about GitHub Actions and the host action: those are true, not
derivable, and generalise to nothing.

---

## A · Who decides

### E1 — State decides. A model is consulted only where state cannot, and the script's answer is the floor.

Routing is a shell script reading issue state. Where judgement is genuinely required — a bare
mention that could be a question or a request, a missing stamp — the script still computes its own
answer first, and the consultation can only improve on it. A failed, skipped, malformed or
`undecided` consultation lands exactly where the script would have gone.

Two corollaries that have each cost a run:

- `undecided` must be a legal answer. An enum of roles alone forces a confident guess, and that is
  worse than the script's, because answering suppresses the notice that would have flagged it.
- A model decides the one thing in doubt and nothing else. The story, its branch and the issue kind
  stay on the script's outputs — letting a model restate them puts two sources on one fact.

The inverse also holds and is easy to miss: where a script *cannot* be right, do not script it. A
regex for "epic" misfires on *"a story under the Claude Team epic"*, and a false positive decomposes
a story into stories. That call is judged.

> Evidence: rule 1b's `consult`; the `defaulted` floor; `'n/a' != 'epic'` on #1112; branch creation
> was the last load-bearing thing a model owned and failed about half the time.

### E2 — Derive from what a role must produce anyway. Never from a block it was asked to leave behind.

A scripted hook fed by model-written courtesy input is still model-driven. The `Branch:` line, the
`### Sequencing` section and the `--json-schema` output are each a deliverable the role owes for its
own sake, which is what makes reading them deterministic.

⚠️ **A line naming a thing is not the thing.** Treating the `Branch:` line as proof of the *branch*
is the same defect wearing the shape of a fix — the line is model-written and the ref may not exist.

> Evidence: epic #1112 — six issues created, zero parented, step green, because parentage keyed on a
> prose `epic #N` reference no prompt required · #744/#777 · trigger order is derived from
> `(phase, number)` rather than stamped, because *"a third stamp naming an order would be a third
> line it could skip"*.

### E3 — Bound a role by what it can reach, not by what it is told. Then check what it needs, because too tight starves it silently.

Both halves are load-bearing and they pull against each other.

The custodian's repair enum is a fixed set a hook applies, which is what makes *"never touches
content"* a fact about what exists rather than a promise in a prompt. Where a bound has to become
instructed instead — the Custodian's direct git, by the maintainer's decision — say what was lost
and what still holds structurally.

The other half: a bound that is too narrow does not fail loudly, it starves the role and burns turns
on permission denials. Check what the role actually needs *before* narrowing. Relationships survived
narrowing the Custodian to subcommands only because `gh issue view` was checked first.

> Evidence: `apply-repairs.py`'s enum · Security taught this package that too narrow starves a role
> silently · the Writer withheld `npm` could not produce the spec it owns · authoring roles granted
> `Bash(npm|npx|node:*)` could not run a Python gate, including in this repo (#46).

---

## B · How a fact travels

### E4 — Every required output has a named reader, and the reader is somewhere someone actually looks.

The most-repeated failure in the record, and it counts itself: `DEFAULTED` as a job output nobody
read; the #475/#476 author handoff appended in a job its readers never run in; `decisions` on the PR
path; `docsCandidates`; `unrepairable` printed to the job log; and `landed_ref`, written to
`$GITHUB_OUTPUT` and given to one step but not the second one that needed it. **Six instances**, each
shipped and believed to work.

Two distinct failures wear this shape, and both are fixed before merging the producer:

- **No reader at all.** Name the consumer, or do not add the output. A job-level output declaration
  with no reader is worse than nothing: it invites the next person to assume something gates on it.
- **A reader nobody reads.** *"A role that answers into a channel nobody reads has not answered."*
  The job log is not a channel. The custodian named a stale title and the role that should fix it —
  a good redirect, written to a job log — and from outside the role had said "not my job".

⚠️ **A decision with no record is worse than a channel with no reader.** With a dead channel you can
at least go and read the producer.

> Evidence: six counted instances · `apply-repairs.py`'s `unrepairable` · the routing interception
> shipped without a transcript, alone among model steps · a test now asserts that **every env var any
> hook reads is set somewhere in `team.yml`** (see E17).

### E5 — Three states, never two: present, explicitly empty, and absent.

`remaining: []` means *"I looked, there is nothing"* — actionable. **No handoff at all** means no
author ran, or its run died before posting. A consumer that collapses the last two treats a failed
run as a clean one.

This is not a handoff rule. It is true of every parsed input:

- Conflating *no commits* with *unfinished* stranded a check-shaped task and halted a story (#1140).
- Conflating *absent handoff* with *empty `remaining`* closed #1159 as "nothing to do" after its
  model step was **skipped**, and dispatched the next wave. That was the *fix* for #1140.
- A `### Sequencing` section that **parses to nothing** is not the same as no section. A ref naming
  something outside the story already warned; a section naming nothing at all did not, so the loud
  signal went to the smaller problem.

⚠️ **An empty result is recorded, never inferred from silence.** "Checked, nothing to do" and "the run
did nothing" are indistinguishable to a reader otherwise.

> Evidence: #1140 · #1159 · `sequencing_refs()` · the schema forces `remaining`, so only an
> **explicit** `[]` closes a task.

### E6 — Upsert what is derived; append what is a record.

A status board, a task list, `remaining`, a routing notice — regenerated whole each run, so replacing
loses nothing. `decisions`, custodian findings, repair history — a later round replacing an earlier
one destroys the fact the comment exists to keep.

The test is not the surface, it is the content: **is this a snapshot or a record?** A repeat finding
must stack, because *a finding that recurs is the signal that its cause is still there*.

> Evidence: #626 deleted on review, #651 reinstated two PRs later by an agent reading a story nobody
> had corrected · the custodian's repeat-escalation reads the log comment, which is why it must
> append.

### E7 — Read a fact from whoever holds it. Never infer it from a proxy.

The sharpest rule here, and the most recently learned.

`finish-pr.py` asked *"did this run produce anything?"* by counting `origin/<default>..HEAD`. But a
landed commit and a stranded one are **byte-identical on the runner** — the only thing separating
them is whether a push happened, which is a fact the landing hook holds and the count does not. So
the hook declared landed work stranded, opened a second PR, and named a ref that dies with the runner
as where the commits were safe. On *every landing that ever worked*.

The same defect, twice more:

- `origin/<named>..HEAD` counts the default branch's own history when the named ref is stale, so a
  correct no-op run announced *"could not land 1 commit(s)"*. A stale-but-ancestor ref was never the
  problem — the measurement was.
- A failed `fetch` was read as *"the ref does not exist"*, so an auth failure presented as a missing
  branch, on the path that then pushes.

⚠️ **Any future "did this run produce anything" predicate must read the landing's own report, not the
graph.**

⚠️ **And a sandbox that is too clean cannot catch this.** A fresh branch hides the stale-ref
arithmetic entirely, so every sandbox that built one passed. Where a bug lives in staleness, build a
stale fixture.

> Evidence: run 32561656056 (#44) · #748 · #1110/#1111 · `work-completion.py`'s fetch.

---

## C · How it fails

### E8 — A sole mechanism fails loudly — and loudly is not the same as usefully.

`open-story-pr.py` needed `pull-requests: write`, had `read`, and 403'd **every time since the hook
existed**. It had never once succeeded: every story PR was opened by hand while `CLAUDE.md` described
the hook as the mechanism. It survived because it emitted a `::warning::`, and a warning fails no
step.

Then it failed loudly for a year with *"open it by hand"* and no cause — on a hook where every benign
path has already returned, so reaching that line always means a PR genuinely should exist and
something refused. Every diagnosis started from zero.

So the rule has two halves:

- **Sole mechanism → fail the step.** Best-effort is right for bookkeeping a human would notice
  missing; it is wrong for the only thing that opens a PR. Structure the hook so every benign case
  returns early, and then reaching the action without performing it is always a real problem.
- **Failing → name the cause.** Not a list of likely causes; the actual reason. `team.gh_raw()` exists
  for exactly this and for nothing else — never parse its stdout, and always `scrub()` it.

> Evidence: the record calls the first half *"the third instance"* of the silent-warning shape · #27.

### E9 — A guard that starts work fails closed. A guard that protects work fails open.

Two halves pointing opposite ways on purpose. The discriminator is what each failure costs.

- **Fails closed:** the dispatch guard is written *positively* — only a kind recognised as workable
  proceeds — so an unresolved kind cannot start anything. Written negatively, `'n/a' != 'epic'` is
  true and an epic's task was dispatched to an Implementor a minute later.
- **Fails open:** the failure capture pushes *anyway* when ahead-ness cannot be determined, because an
  empty branch is noise and a lost capture is the thing the hook exists to prevent. Likewise an
  unreadable task list degrades to open-when-ahead: *an early PR is a nuisance, a story that can never
  get its PR is lost work.*

Starting work nobody asked for is unbounded. Leaving debris is one line of noise.

> Evidence: #1112 · `capture-failure.py` · `open-story-pr.py`'s degraded path.

### E10 — Never write a message that tells the reader to stop looking.

A failed landing said *"the commits are safe on `<runner branch>`"* — a ref never pushed, which dies
with the container. The capture wrote *"your changes are preserved on `failure/…`"* for a branch
byte-identical to the default, handing the reader a recovery command that produces a clean checkout.
A **successful** landing said it too.

Every lost-work incident in this repo's history was caught because *something looked wrong*. A
reassuring message is the one defect that removes the mechanism by which its own class of defect gets
found — which is why it outranks being merely wrong.

> Evidence: run 31918402971 · run 32561656056 (#44) — two `::error::` lines for one fault, and the
> louder one was the false one.

---

## D · What it may not do

### E11 — Nothing destroys.

No force-push. No reopening a landed task. No closing a merged story's open children — that hid
exactly the case worth seeing. No rewriting someone else's evidence: the Architect **appends** to a
bug report because its body is an investigation that already happened, and the Researcher **appends**
to a spike because its body is the question itself. A rejected landing reconciles by merge; a
conflicted merge fails the step and hands resolution to a human.

The sole deletion requires **two independent conditions**: 0 commits ahead of the default branch, and
the issue closed. Either alone is wrong — 0-ahead by itself deletes a story branch whose first task
has not run.

⚠️ **A deletion is announced on the issue, not just logged.** A branch that vanishes with no record is
indistinguishable from one that was never created.

> Evidence: the branch sweep shipped and was removed one PR later; its note is kept deliberately (W3).

### E12 — Fix and report, never fix quietly. A repeat escalates instead of repairing.

Every repair appends what was wrong and why. Reaching for the same repair kind on the same target
twice means the cause was never fixed, so the hook **withholds** the repair, files an issue, and
leaves the instance broken on purpose.

*"The value of this system has come from breakage being visible: a 404 nobody hid is what produced the
rule that prevents it."* A custodian quietly repairing the same thing weekly has become a suppressor
of the signal that would have fixed it properly.

`unrepairable` is the half that carries the weight — anything outside the enum, anything needing
content changed, and anything whose real fix is upstream in a rule. Keeping it separate is the point.

> Evidence: `apply-repairs.py` · the repeat check reads the log comment, which is state on the issue
> rather than a memory of the last run.

---

## E · How instructions behave

### E13 — Two absolute instructions that can conflict will be silently disobeyed. State precedence, or scope one so they cannot meet.

**Five instances, and every one was resolved by a run picking a side without saying so.**

| the pair | what the run did |
|---|---|
| *"open your PR against the story branch"* + *"never commit to the story branch"* | invented a third branch and a second PR to escape |
| Designer: *"stay inside the design system"* + *"hand over a green gate"* | disobeyed one silently |
| *"a one-author story should not be split"* + *"a Writer task on **every** story"* | disobeyed one silently (#47) |
| host action's injected *"do not create a new branch"* + our prompt telling it to cut one | went both ways, about 50/50 |
| an issue's worked example + a standing rule about how to work | followed the example 17 times (#746) |

⚠️ **The scope is the fix; softening the rule is not.** Turning either absolute into *"use judgement"*
reverts to the failure that produced the rule. What changes is **which decision the role is making** —
the Writer rule was rescoped to stories that divide, a question the Architect was answering anyway,
rather than *"does this deserve a spec"*, which it answered wrong every time it was asked.

⚠️ **Where precedence is the answer, write it down.** An issue says *what* to deliver and ages in
place; a rule about *how to work* is newer and wins.

> Evidence: #47 · #746 · the extra-PR contradiction, which the record notes *"was ours"* — the host
> action had been right all along.

### E14 — A worked example outranks the prose around it. Test your examples.

The Architect prompt demonstrated `**Sequencing.** Its tasks run in order: #606, then #607, then
#608.` — which matches the heading, puts its refs on the heading line, and parses to **zero waves**.
Two sibling stories shipped that form and both silently fell back to derived order.

⚠️ ***The parser was never wrong; the instruction was.*** Prose review had already passed this twice.

The same shape elsewhere: `file-sub-issues.py`'s first version adopted a meta-issue that *quoted the
convention as an example*; an epic's Sequencing section is legitimately prose while the identical form
on a story is the defect, so a test pins both **so nobody harmonises one example to match the other**.

> Evidence: a test now parses every Sequencing example in the prompt · #746's `chromium.launch(...)`
> snippet, followed 17 times against a prompt that said otherwise.

### E15 — A run ends with a deliverable or a named obstacle. Never an intention, never an invention.

Three failure shapes, and no single discriminator catches all three:

| shape | what it looks like | the discriminator |
|---|---|---|
| **stops early** | a tidy checklist, boxes unticked | the cause is *backgrounding* — work delegated to a continuation that never comes, not idling |
| **stops late** | 81 turns grinding one obstacle, nothing written | non-convergence: variations on the same obstacle rather than steps forward |
| **gathers without producing** | every turn succeeds and yields something new; the deliverable is empty | **what is in the file I was asked to produce**, not *am I learning things* |

⚠️ **Stopping is not permission to invent** — that is the failure the stop exists to avoid, and it is
worse than either, because nothing about it looks wrong.

⚠️ **Ambiguity is not a stop condition.** *"Confirm scope"* is the tell: a plan step whose natural
completion is asking a human has planned its own failure, because nobody is reading while a run
executes. Choose a defensible reading, ship, and raise it in the 🔔 Maintainer section.

⚠️ **No issue body can require a role to spend the whole budget.** An unmeetable acceptance criterion
is a finding. Across five runs on one story the first three reported precisely what blocked them in
1–4 minutes and the last two ground to the cap with nothing.

> Evidence: #834 · #866 · #1018 (the captured transcript that showed backgrounding) · #746 — 17 driver
> scripts, 20 screenshots, 81 turns, no specification.

### E16 — Do not correct a default by removing the capability.

The stall in E15 was caused by a background-subagent tool, and forbidding delegation outright would
have been the wrong fix: a subagent invoked in-turn returns its result and works correctly. The rule
names the **behaviour** (backgrounding) rather than the feeling (giving up).

⚠️ **And the general rule did not bind.** *"Never end a run with an intention"* was already there; the
model did not think it was ending on one — it believed it had scheduled a resumption, and the tool
call had returned success. A rule aimed at the feeling misses the mechanism.

> Evidence: #1018 · a denylist was not available either — the tools were in **neither** the role's
> allowlist nor the action's base set and executed anyway, which is a finding in itself.

---

## F · Where a rule lives, and what enforces it

### E17 — An instruction is the weakest enforcement available. Prefer a check; once a rule has been broken twice, assert it in the suite.

*"These were prompt instructions until a model skipped them. A scripted step costs no turns and cannot
be forgotten."*

The prompt is the second line of defence, not the first: the custodial phase **fails the run** when a
deliverable is missing, because for as long as that went unnoticed it reported success. Neither
replaces the other — the check is how anyone finds out, the prompt is what stops it happening.

And where prose review has already let something through twice, stop restating and start asserting.
Five rules here are now suite-enforced rather than documented:

- every Sequencing example in the prompt is parsed
- both Sequencing forms are pinned, so nobody harmonises one to the other
- every env var any hook reads is set somewhere in `team.yml`
- the schemas contain no single quote and survive being compacted to one line
- the warning block's wording never reads as a closing keyword

> Evidence: `tests/test_workflow.py` · a var read and never set can only ever be empty, and that is
> checkable without knowing which step should set it.

### E18 — Nothing in the package names a consuming repo. Not its gate, its paths, its packages, or its toolchain.

The one property that makes this portable. `prompts/`, `hooks/`, `schemas/` and `.github/` may not
name a repo, its branches, its gate, its packages or its paths — which is also why
`docsCandidates[].file` is a free string and never an enum of one repo's layout.

⚠️ **A toolchain is the same category as a gate**, and that took a violation to see. Every authoring
role was granted `Bash(npm|npx|node:*)` and nothing else, so an author in a Python-gated repo could
not run the gate at all — including in this repo. The symptom is a role producing a change it cannot
verify, reported in a section easy to skip.

`.claude-team/` is the exception and the point: a rule that would be true in any repo belongs in the
base, a rule that names a command, a path or a package belongs in the overlay.

> Evidence: #46 · the `runtimes` input · `ReleasePins` and `SelfInstall`.

### E19 — Move when a check runs before making it cleverer. Observe at the back only what the front genuinely cannot know.

*"Does this story have tasks?"* read 0 for **every** story while branch creation ran before
`file-sub-issues.py`. The first attempt was a back-half observation; the actual fix was moving the
Architect's call to *after* the parenting hook, which dissolved the question rather than deferring it.

Some questions really cannot be answered at the front — *"was this branch ever used?"* is not knowable
until work lands or does not; *"did the Architect deliver?"* only once it has stopped. Those belong at
the back. But reach for **when it runs** before reaching for either a cleverer predicate or a later
one.

> Evidence: the front/back split for `branch-navigation.py` is gone; it is one hook at every site.

---

## Rules for writing rules

The record's *form* is as load-bearing as its content. These are the conventions that make a ⚠️
paragraph worth keeping.

### W1 — A rule earns its place by a measured failure, not by taste.

Run numbers, issue numbers, what it cost, how long it ran. A ⚠️ that argues from principle alone is a
preference wearing the marker's clothes.

### W2 — Name the wrong fix, not just the right one.

Half the value here is closing off the attractive wrong turn: *"the obvious fix is worse"*,
*"`git-push.sh` is NOT the fix"*, *"a denylist is not available"*, *"taking the secret away is not
available, and that was the first fix attempted"*, *"anyone reaching for that fix should stop here"*.
A rule that only says what to do gets re-litigated by the next person who has the bad idea.

### W3 — A superseded rule stays, with what was tried and why it failed.

The obsolete branch-sweep note is kept on exactly this basis. *"This paragraph used to say the
opposite"* is a sentence worth writing. Deleting a wrong rule deletes the reason nobody should try it
again.

### W4 — Two paragraphs that look redundant are usually two failures that presented alike.

Do not merge on similarity. The second one is generally why the rule survived contact with the first
fix — #1159 is the fix for #1140 reproducing the same shape one level down.

### W5 — State the discriminator, not the feeling.

*"The two halves read as a contradiction unless the discriminator is stated."* Name the behaviour
(backgrounding), not the mood (giving up). Name the test (*does a specification need writing before
the code?*), not the judgement (*does this deserve a spec?*) — a role asked the second question
answered it wrong every time.

### W6 — Count the instances, out loud.

*"The fifth instance of this exact shape."* *"This is the sixth dead channel here."* *"Since this is
the third instance."* A counted recurrence is the argument for changing the **mechanism** rather than
the wording — and it is what tells you when W7 applies.

### W7 — Twice is the threshold. After that, assert it instead of restating it.

This is E17 turned on the rule writer. *"Prose review had already passed this twice"* is the sentence
that should trigger a test rather than a stronger adjective. *"This trap survived being documented and
was written again anyway, twice"* is the same signal, unheeded.

### W8 — Say what it cost, and what accepting it costs.

*"The cost, accepted: a story branch that exists even when a run produces nothing."* *"Chosen with the
cost stated."* *"With the accepted cost that a hand-written sub-issue is never auto-parented."* A rule
whose price is unstated will be reversed by whoever next pays it.

### W9 — An example inside a rule is itself a rule. Test it.

E14 applies to this file too. Any worked example here that a script could parse should be parsed by
the suite, or it will drift from the prose around it and win.
