# claude-team

A portable Claude + GitHub agent team: the role prompts, the scripted hooks around them, and the
workflow that runs them. Extracted from `brewdocs.beer`'s `packages/claude-team` (design and
phases: `matt-whitaker/claude-code#34`).

⚠️ **The gate is the test suite**: `python3 -m unittest discover -s tests` — stdlib only, no
dependencies, runs anywhere. The harness copies each hook into a scratch directory beside a
scripted `team` stub (Python resolves imports from the script's own directory before PYTHONPATH,
which once silently shadowed a stub), imports the pure text helpers from the *real* `team.py` so
they cannot drift, and runs every git-touching case against real repositories — including
deliberately stale refs, the condition sandboxes kept lacking.

⚠️ **Releasing**: check out mainline, rename `CHANGELOG.md`'s `## Unreleased` heading to `## vN`
and open a fresh empty one above it, flip every pin (`TEAM_REF`, the in-workflow `@refs`,
`load-prompt`'s default, the stub template) from `mainline` to `vN` in one commit, run the suite
(`ReleasePins` asserts the agreement), tag that commit `vN`, push the tag, and **do not merge the
release commit** — mainline keeps its canary pins. Consumers pin `@vN`; a repo whose job is to
exercise the engine tracks `@mainline` instead — brewdocs.beer as the canary, `claude-team-example`
as the drill target, and this repo's own stub, which `SelfInstall` pins there permanently.
⚠️ **A RELEASE IS NOT FINISHED WHEN THE TAG IS PUSHED — the consumer half was never written down
at all.** `ONBOARDING.md` installed and never re-installed: every step was written for a fresh
target, so a session pointed at an installed repo had no instruction for the case it was in, and
"upgrade" meant bump the ref and hope. §0 is that path, and `CHANGELOG.md` is what makes it
answerable.
⚠️ **THE CHANGELOG IS CONSUMER-FACING OR IT IS WORTHLESS.** A list of merged PRs cannot answer the
only question a consumer has — *must I act?* — so every version heading carries an explicit
`**Action required:**` line and a test asserts it. `no` is the commonest answer and the most
valuable one.
⚠️ **A file rather than the tag's GitHub release notes**, which was the open question. Three
reasons, and the third is the deciding one: a session doing an upgrade is already in the clone; a
release note needs a network call and an API that can drop mid-session; and **a file is testable**,
which is this package's standard for anything load-bearing. `python3 -m unittest` cannot assert
anything about a release note.
⚠️ **The entry is written in the PR that causes it, not at release time.** Reconstructing consumer
impact from a merge log is exactly the work the file exists to remove, and it is done worst by
whoever is trying to cut a tag — which is why `## Unreleased` stays permanently open. ⚠️ `v1.1`'s
entry says *unknown* rather than a summary written backwards; 24 commits separate it from the next
entry and inferring their impact after the fact is the guesswork this replaces.
⚠️ **AND A PIN CANNOT EXPRESS REPO STATE, which is the half no version number reaches.** Labels
live in GitHub, not in the clone — so no ref bump has ever touched them, and this repo's own
`story` and `task` sat identical at `0E8A16` with empty descriptions while `templates/labels.json`
said otherwise. The one step already written to be idempotent is the one that drifted, because
nothing told anyone to re-run it. §0 re-runs it unconditionally, along with the board and the
Actions settings.
⚠️ **An overlay that contradicts a tightened base rule is the other thing a bump cannot fix.** An
overlay composes *after* the base and therefore **wins**, so a base change narrowing what a role
may do reaches nothing while the overlay still grants it. Measured: the Writer's scope was
corrected here and two consumer overlays went on granting it. §0 says to grep for the old grant
whenever an entry reports a narrowed scope.
⚠️ **brewdocs.beer-kb tracks `@mainline` without that justification** — it ships product, so the rule
says pin it. Kept on the edge by the maintainer's call, provisionally.

⚠️ **The consumer contract**: `team.yml` is a reusable workflow (`on: workflow_call`). A consumer holds
the frozen stub (`templates/consumer-stub.yml`) plus a `.claude-team/` directory — `prompts/`
overlays (`_shared.md` required) and an optional executable `setup.sh`. Inputs: `project_owner`,
`project_number`, `allowed_bots`, `node`, `browser`, `runtimes`. ⚠️ **Two pins move together**: the consumer's
`@ref` on the workflow, and `TEAM_REF` inside it (what the jobs fetch at run time) — release
tooling owns keeping them equal.

**Purpose.** A portable Claude/GitHub role team: the prompts each role runs on, the scripted
hooks around them, and the handoff contract between them. Consumed by pointing a workflow at
these files; extended by a per-role overlay in the consuming repo.
**Where.** `prompts/_shared.md` + `prompts/<role>.md`, `hooks/*.py`, `schemas/handoff.json`.
**Invariants.** Nothing here names a consuming repo, its branches, its gate or its packages.
**[E1]** Routing is a script first: state decides wherever state can, and a model is consulted only where it cannot — a bare mention that could be a question or a request, a stamp that is missing — with the script's own answer as the floor when the consultation fails. Every hook is deterministic and derives its input from
state, not from something a model was asked to leave behind.

⚠️ **`RULES.md` names the rules these paragraphs are instances of.** This file is the record —
what went wrong, measured, and what was done about it. That one is the short list the record keeps
re-deriving: the dead channel found six times, the guard direction, the proxy measurement, the two
absolutes a run can only obey by disobeying one. It also carries the conventions for writing a ⚠️
paragraph at all.
- A paragraph cites its rule by opening with the id — `⚠️ [E4] **…**`. **Tag as you go**: a
  paragraph picks one up when someone next edits it, and an untagged paragraph is not a defect.
- A **new** ⚠️ paragraph cites a rule, or says plainly that it is a new one and adds it there in the
  same commit.
- `RuleIds` in `tests/test_rules.py` fails on a citation that resolves to nothing.

⚠️ **A cloud session should read `CLAUDE_CLOUD.md` first** — what a local session gets from
memory and `~/.claude/`, which do not reach a cloud container at all. It is mentioned in backticks
deliberately: an unbackticked `@path` is a real, unconditional import, and importing it would load
cloud-only instructions into every local session.

## The issue hierarchy

| level | branch | its PR targets | closed by |
|---|---|---|---|
| **Epic** | none | — | its stories closing |
| **Spike** | none | — | the maintainer, once they have decided |
| **Story** | `<story#>-<summary>`, cut by the Architect | the **default** branch | its PR merging |
| **Task** | none of its own — its work lands on the story's branch | — | `work-completion.py`, once its work has landed |

- An epic never has a branch and never has a PR. If something needs a PR, it is a story.
- ⚠️ **An unprocessed issue is a STORY.** An epic has to say so — by an `epic` label or a
  title beginning "Epic" — and the Architect leaves both markers behind so nothing re-derives
  it next run. Deliberately NOT inferred from having sub-issues: a story has those too, they
  are its tasks. The old inference only held because a shaped story also had a branch, so an
  unshaped story with tasks read as an epic.
- ⚠️ **A maintainer's comment is the only override**, and it is judged by the model rather
  than matched by the script. A regex for the word misfires on an ordinary sentence — "a
  story under the Claude Team epic" — and a false positive decomposes a story into stories.
- ⚠️ **Epics are the maintainer's to create.** No role files one on its own initiative and
  none promotes an issue into one. A role may *propose* an epic and stop; the decision is
  not delegated. Ambiguity resolves to a story, always.
- ⚠️ **A `spike` is a question, and it is the one unshaped issue the Architect must not take.**
  Its answer is not known yet, so there is nothing to decompose — handed one, the Architect cuts
  implementation tasks for a solution nobody has chosen, which reads like progress and is worse
  than nothing because the tasks then get worked. `delegate.py` rule 3 routes it to the
  **Researcher** instead. Like an epic it has no branch, no PR and ships no code; unlike an epic
  it is not a container, so it has no children either. `team.kind()` detects it from a `Spike:`
  title or the `spike` label, and **epic still wins** when an issue carries both.
- ⚠️ **A `bug` is a story in shape but not in handling.** One branch, one PR, usually one task
  — but its body is the deliverable of an investigation that already happened, so the Architect
  **appends and never rewrites**. A report's reproduction, its measurements and especially its
  "what I could not determine" section are the only grounding the fixer has; a story-shaped
  rewrite replaces evidence with an opinion. `team.kind()` returns `epic | bug | story`, and
  **epic wins** when an issue carries both markers, so it resolves the same way every time.

⚠️ **Two kinds of label, and only one is the maintainer's.** "Create issues unlabeled" reads as
covering both, and it does not:

| kind | labels | who applies | what it means |
|---|---|---|---|
| **routing** | the front-door label, `@claude/<role>` | the maintainer; hooks stamp the trail | what should *happen* to this issue, and what has already run |
| **classification** | `epic`, `spike`, `bug`, `task`, `story` | anyone filing; the custodial phase fills gaps | what this issue *is* |

A classification label is durable and derivable, so it survives a run and nothing has to
re-derive it. ⚠️ **Every kind gets one, `story` included.** An earlier version left a story
unlabelled and treated the absence as the signal — which reads fine inside a hook and badly on
a board, where you cannot filter for "the ones with nothing". `team.kind()` still *derives*
story from the absence of the other markers; the label is what makes that visible.

⚠️ **`task` IS DERIVED FROM STRUCTURE, NOT A MARKER, and needs no new stamp.** A task's `Branch:`
line names its **story's** branch, so the number it starts with is not its own; a story's names
itself. `kind()` uses exactly the test the PR-base rule uses, so the two cannot disagree about what
a task is. ⚠️ It is checked **after** the marker kinds: an `Epic:`/`Spike:`/`Bug:` title is an
explicit statement, a branch line is an inference, and the explicit one wins.

⚠️ **The custodial phase labels the TASKS; the trigger-time pass only ever reached the trigger.**
That hook runs against the issue that triggered the run, so a story got a label and the tasks the
Architect had just created never did — and tasks are the most numerous kind. The back half runs
after `file-sub-issues.py`, which is the first moment those children are discoverable at all. It
only ever **adds**: an issue already carrying a kind is left alone, because a maintainer who
relabelled something by hand meant it.

⚠️ **`spike` stays a kind even though it looks redundant beside `story`.** It is not cosmetic:
`delegate.py` rule 3 routes a spike to the **Researcher** rather than the Architect, because an
Architect handed an open question decomposes a solution nobody has chosen. Removing it changes
routing, not labelling.

⚠️ **The kind pass (`labels-and-status.py MODE=kind`) asks `kind()`, not the title.** Keying on the title worked only while
every kind announced itself — a story has no prefix to match and would never have been labelled.
⚠️ And it refuses to write when it cannot read the issue: `kind()` falls back to `story` on a
failed API call exactly as it does for a plain issue, so a rate-limited minute would otherwise
relabel an epic. It only ever adds, never removes.
- A story owns one branch and one PR against the default branch, and it accumulates.
- A task is a slice of a story. It has **no PR**; its commits land on the story's branch.

⚠️ **The Branch line always names the STORY's branch** — on the story and on every one of
its tasks. It is what an author bases on and merges back into, never a branch for the task
itself. Anything deriving a story from a branch name reads that prefix.

⚠️ **A story's Branch line carries a compare link**, appended by `branch-navigation.py` after
the closing backtick, so opening its PR is one click instead of a walk through the UI. One link
serves the branch's whole life — GitHub redirects a compare URL to the existing PR once one is
open. ⚠️ The link sits **outside** the backticks because `branch_line` is anchored and captures
only what is between them; that is deliberate, not luck, and trailing text must stay outside.

## Sequencing

⚠️ **Stories are independent; a story's tasks are ordered.** Two different defaults, and each
must be stated where it can be seen:

- **Between stories** — independent unless the **epic's own body** says otherwise. A dependency
  written only in the dependent story is not enough: #603's body opened with "Depends on #602
  landing first", the epic said nothing, #603's tasks were started while #602's PR was open, and
  its Tester found no feature to test.
- **Within a story** — the Architect's `### Sequencing` section is the contract: numbered lines,
  one wave per line, several refs on a line running in parallel. `dispatch-next.py` consults it to
  start the next wave; a task the section forgot is appended in derived `(phase, issue number)`
  order rather than stranded, and with no section at all tasks run one at a time in that derived
  order. The same section is what the human reads when driving by hand.
  - ⚠️ **A SECTION THAT PARSES TO NOTHING IS NOT THE SAME AS NO SECTION, AND FOR ONE RELEASE BOTH
    WERE SILENT.** `sequencing_refs()` only reads refs from lines that *start* with a number, so a
    section written as prose — *"Its tasks run in order: writer, then implementor, then tester"* —
    reads correctly to a human, satisfies any check looking for the heading, and carries no
    instruction at all. A ref naming something outside the story already warned; a section naming
    **nothing** did not, so the loud signal went to the smaller problem. Both callers now say so,
    and the fallback to derived order is deliberately kept — falling back is right, doing it in
    silence is what cost the diagnosis.
  - ⚠️ [E14] **THE ROOT CAUSE WAS THE ARCHITECT PROMPT'S OWN WORKED EXAMPLE.** It demonstrated
    `**Sequencing.** Its tasks run in order: #606, then #607, then #608.` — which matches the
    heading, puts its refs on the heading line, and parses to zero waves. Two sibling stories
    shipped that form with roles instead of numbers and both ran on derived order. The parser was
    never wrong; the instruction was. ⚠️ A test now parses every Sequencing example in the prompt,
    because prose review had already passed this twice.
  - ⚠️ **THE NUMBERED FORM IS CONTAINMENT, NOT DOCUMENTATION**, which is the reason this is worth
    fixing rather than filing as cosmetic. A task the section forgets is appended *after* the
    listed waves, deliberately — so a task mis-parented onto the wrong story runs last. With the
    section inert everything falls to derived order, that foreign task sorts by its role phase, and
    a stray `writer` dispatches **ahead of the story's own implementor**. Measured on a consumer at
    `v1.1`: the prose form is what turned a filing error into a dispatch-order error.
  - ⚠️ **AN EPIC'S SECTION IS PROSE AND THAT IS CORRECT** — two forms, two parsers, and one looks
    exactly like the trap. `file-sub-issues.py` takes any `#N` on any line of an epic's section, so
    the inline form is legitimate there; the identical form on a *story* is the defect above. The
    custodial check is therefore scoped behind the epic/spike return, and a test pins both so
    nobody harmonises one example to match the other.
  - ⚠️ **THE FIRST WAVE NEEDS ITS OWN IGNITION, and for one release it had none.** The hook chains
    task N to task N+1 from the authors job, so a story could be *continued* but never *begun* —
    the maintainer still hand-labelled task 1, which is the gesture the cascade existed to remove
    (#1095). It now also runs **post-Architect**, once a freshly-shaped story has its branch, and
    **inside `delegate`** for a story that arrives already shaped. Three call sites, one hook: it
    finds the earliest incomplete wave, so "the first wave" is just the general case with nothing
    closed yet.
  - ⚠️ **A DARK CASCADE MUST SAY WHY, AND FOR ONE RELEASE IT COULD NOT.** The dispatch step
    required a non-empty token in its `if:`, so a mint that FAILED produced a silently *skipped*
    step — and `continue-on-error` on the mint reports `conclusion: success`, so a broken cascade
    and a deliberately-dark one were indistinguishable from outside. Measured on run 31928714016:
    every step green, the task landed and closed, the next task never started, nothing anywhere
    said why. ⚠️ The token check now lives in the **hook**, which separates the two cases by
    volume — no secrets is the configured-off state and stays a `::notice::`; secrets present with
    no token is a misconfiguration only a human can fix and is an `::error::`. The commonest cause
    is an App that is authenticated but **not installed on the repository**, whose signature is a
    404 on `get-a-repository-installation-for-the-authenticated-app`.
  - ⚠️ The Architect's call sits **after** `branch-navigation.py`. A task's run bases on the story
    branch, and dispatching before that ref exists reproduces #744 — the authoring job 404s in
    ~3s, before the model is called.

⚠️ **"Depends on" means MERGED.** A story whose tasks are all closed but whose PR is open has
delivered nothing to any other branch — which is why the epic's work log carries a **landed**
column beside the task count. `2/2 tasks` and `PR #629 open` are different facts, and only
showing the first is what allowed this to happen.

⚠️ **Branch creation is scripted, not prompted** — the last load-bearing thing a model owned,
and it failed about half the time. The host action mints its own branch for an issue trigger
and injects *"You are already on the correct branch. Do not create a new branch"*, which
contradicts any prompt telling a model to cut one. Which instruction wins is the model's call,
and it went both ways. Three pieces replace it:

- **The story branch** — a **post**-hook reads the `Branch:` line the Architect had to write
  anyway and creates that ref at the default branch's head. The Architect names it and
  nothing else.
- **A task's branch** — the action's own `base_branch` input, set to the story's branch. The
  branch it creates is then the right one, so its injected instruction becomes true instead of
  something to argue with. Configure the action rather than fight it.
- **A task's commits** — `work-completion.py` commits and lands them on the story branch. There is no task
  PR and no base to get wrong, so the whole retarget-and-net apparatus is gone.

⚠️ **The story-branch hook must run POST, and this inverts the obvious implementation.**
`setupBranch` checks whether the name it is about to generate already exists remotely and, if
so, discards the configured template and falls back to `claude/<entity>-<n>-<timestamp>`. A
pre-hook pushing the story branch would collide with the very name the action mints from
`{{entityNumber}}-{{description}}`, stranding the run on a branch nobody looks at. Orphaned
`claude/*` branches in a consuming repo are this fallback firing on a re-run.

⚠️ **The hook never touches a branch that exists.** Absent is the only case it handles: an
existing branch may carry an author's commits, and resetting it to the default branch would
destroy exactly the work the hook exists to protect.

⚠️ **A story implementable as-is is not a task, and its PR targets the DEFAULT branch.** The
test is scripted, not judged: a task's `Branch:` line names its *story's* branch, so
`story_from_branch(named) != ISSUE`; when they are **equal**, the executing issue owns that branch
and its work is the whole story. There is no parent for it to merge into.

⚠️ **AND THE ARCHITECT MUST BE TOLD IT MAY PRODUCE ONE, WHICH FOR A LONG TIME IT WAS NOT.**
`prompts/_shared.md` described the as-is story from the **author's** side — *"You are a STORY
worked as-is"* — which tells a role what it *is*, never that shaping may end there.
`prompts/architect.md` was silent on it, so the prompt described two of the three shapes
`delegate.py` routes: a story with tasks dispatches its first wave, one with no tasks falls
through to its stamped author, and one with neither stamp nor tasks defaults to the Implementor
and announces the guess on the issue at **every** trigger.
⚠️ **It worked anyway once, and that is what hid it.** The Architect on #43 reached the right
shape by citing **CLAUDE.md** — this repo's own file, which in a consumer belongs to the consumer
and says nothing of the sort. Behaviour that depends on the package being its own consumer is not
portable, and the drill only passed because the answer happened to be lying around.
⚠️ **The stamp is the expensive half.** A Branch line with no Role line is the one shape that
costs a run before any work starts, and it recurs on every trigger rather than once.

⚠️ **Retargeting one of those onto its own story branch is the failure**, and it looks like
correctness. The work lands on a branch nobody has merged, `close-merged-work.py` closes the story
on that merge anyway, and finishing it then needs a second PR for an issue that is already closed —
which is also why the two cannot simply be linked. Measured on #751: its story branch was **empty**,
the real work sat one branch further down, and the PR pointed at the empty branch.

⚠️ **The doubled branch is not the thing to fix, and the obvious fix is worse.** `setupBranch`
always *creates* a branch on an issue trigger — it has no mode that checks out an existing one, so
a second branch is structurally guaranteed and the author cannot avoid it. Making the story branch
itself the working branch would mean not pre-creating it, and **the old pre-parenting hook ran before
`file-sub-issues.py`**, so at that moment `sub_issues()` returns 0 for *every* story — including one
the Architect just decomposed. That test cannot be evaluated there, and acting on it would strand
every story with no branch at all. Changing the PR's **base** costs none of that.

⚠️ **TASKS SHARE THE STORY'S BRANCH, AND THIS PARAGRAPH USED TO SAY THE OPPOSITE.** Sub-branching
with a PR per task was correct about the race and wrong about the cost: one story became one PR per
task plus its own, splitting the only review anyone actually performs across several places. The
maintainer's call was that review sanity beats the guarantee. What replaces the guarantee:

- ⚠️ **The race is real and CANNOT be closed.** `concurrency.group` is keyed on the issue, and it
  cannot be keyed on the story — the group is evaluated before any job runs, so only the event
  context is available, the story is not resolved yet, and expressions have no regex to pull it
  from the issue body. Anyone reaching for that fix should stop here.
- ⚠️ **"DID THE RUN PRODUCE ANYTHING" IS MEASURED AGAINST WHERE THE RUN STARTED, NOT THE NAMED
REF.** For a **task** the two coincide — its base *is* the story branch — which is exactly why the
distinction went unnoticed. An **as-is story** is cut from the default branch while its named ref
may be days old, so `origin/<named>..HEAD` counts the default branch's own history and is non-zero
however little the run did. Measured on #748: a Writer correctly changed nothing, and the landing
announced *"could not land 1 commit(s)"* and a merge conflict against a ref from four days earlier.
⚠️ **A fresh branch hides this entirely**, so every sandbox that built one passed.
⚠️ **A stale-but-ancestor ref is NOT itself a problem** — checked against real repos: the push
fast-forwards. Staleness only ever surfaced through the wrong measurement.

⚠️ [E10] **A FAILED LANDING MUST NOT NAME THE RUNNER'S BRANCH AS SAFE.** It said *"The commits are safe on
`<runner branch>`"* — a ref that is never pushed and dies with the container. Nothing was safe
there. ⚠️ The same defect in the capture: it pushed unconditionally and wrote *"your changes are
preserved on `failure/…`"* even when that ref was byte-identical to the default branch, handing the
reader a recovery command that produces a clean checkout. **A message that tells someone not to
look further is the most dangerous thing this system can write**, and every previous lost-work
incident here was caught precisely because something looked wrong. ⚠️ The capture now **fails open**:
when ahead-ness cannot be determined it pushes anyway, because an empty branch is noise and a lost
capture is the thing the hook exists to prevent.

⚠️ [E7] **AND A SUCCESSFUL LANDING SAID IT TOO, WHICH IS WORSE.** `finish-pr.py` finds no PR for the
run's branch — correct, the story's PR is `open-story-pr.py`'s to open — and then asks whether the
run produced commits by counting `origin/<default>..HEAD`. `work-completion.py` has already pushed
those commits onto the story branch and **the runner's branch still carries them**, so that count
is non-zero on every landing that ever worked. The hook therefore declared landed work stranded,
pushed the throwaway branch, opened a **second** PR for work that already had one coming, and named
the runner's branch as where the commits were safe. Measured on run 32561656056: two `::error::`
lines for one fault, and the louder one was the false one (#44).
⚠️ **THE DISCRIMINATOR ALREADY EXISTED AND HAD ONE READER.** `work-completion.py` writes
`landed_ref` to `$GITHUB_OUTPUT`; the workflow read it to set `BASE` for `open-story-pr.py` and
never gave it to this step, so the hook saw an empty string forever. **This is the sixth dead
channel here** — after `DEFAULTED`, the author handoff, `decisions` on the PR path,
`docsCandidates`, and `unrepairable` — and the first where the channel had a reader and simply
missed a second one, which is why nothing looked wrong. ⚠️ A test now asserts that **every env var
any hook reads is set somewhere in `team.yml`**: a var read and never set can only ever be empty,
and that is checkable without knowing which step should set it.
⚠️ **Counting commits cannot answer this and never could.** A landed commit and a stranded one are
byte-identical on the runner; the only thing separating them is whether a push happened, which is a
fact the landing hook holds and the count does not. ⚠️ Any future "did this run produce anything"
predicate must read the landing's own report, not the graph.

⚠️ **A rejected landing reconciles by merge**: `work-completion.py` pulls latest, commits the
  merge commit, and pushes. A merge that **conflicts** is not resolved by script — the step fails
  with `unlandable=true`, the commits stay on the run's branch, and resolution is an Implementor
  call. Never a force-push, never silence.
- **Trigger a story's tasks one at a time**, which the sequencing rules already say.

⚠️ **A task still gets a branch, and it is unavoidable rather than intended.** `setupBranch` always
*creates* one on an issue trigger — it has no mode that checks out an existing branch — so a run
cannot start on the story branch. That branch is a staging area: the hook pushes its commits onto
the story branch afterwards. ⚠️ **Nothing deletes it.** After landing it is 0-ahead and harmless,
and adding a delete would put back the one destructive capability this system removed on purpose.

⚠️ **Nothing gates a task any more, and that was chosen with the cost stated.** Verify runs on
`pull_request`; with no task PR it first fires on the story's PR, with every task's diff
accumulated — which is exactly what a consuming repo's no-branches-filter comment was written to
prevent. A `push:` trigger restores it and was declined.

### Where work goes, and why there is only ever one PR

⚠️ **The governing rule: work goes on the branch of the thing the run was triggered on.** Not a
branch the model picks, not a new one. Two modes fall out of it — an **issue** trigger means a
fresh task branch and exactly one PR into the story; a **PR** trigger means commit to that PR's
branch and open nothing.

⚠️ **The host action already implements this; only the prompt ever disagreed.** `setupBranch`
checks the PR's state, and for an **open** PR it checks out `headRefName` and **ignores
`base_branch` entirely** — that input is read only on the create-a-branch path, which is reached
for an issue trigger or a closed/merged PR. So a follow-up run is put on the right branch before
the model gets a turn.

⚠️ [E13] **The contradiction that produced the extra PRs was ours.** The prompt told every run to "open
your PR against the story branch" and, in the same breath, "never commit to the story branch
itself". On a comment against the *story's own PR*, the checkout puts the run on the story branch —
so both instructions were wrong at once, and a run obeying them had to invent a third branch and a
second PR to escape. Committing to the story branch is **correct** when the story's PR is what is
being discussed; the no-commit rule belongs to task runs, which have their own branch.

⚠️ **More PRs is not more granularity, and that is the actual argument.** A reviewer follows a
conversation by reading its commits as small diffs, in order, in the place the discussion is
happening. A second PR splits that thread and makes them reassemble it. The commits already are
the granularity — an extra PR only adds a seam.

⚠️ **No hook opens a second one either**, and that is worth knowing before someone "fixes" it:
`finish-pr.py` resolves the PR from the current branch, so on a follow-up it finds the existing one
and its stranded-commit recovery never fires. That recovery is for a run that committed and left
*no* PR at all.

## How a story moves

1. **Architect** shapes the story, **names** its branch on a `Branch:` line, and creates its
   tasks — each stamped with the role that should pick it up. A hook creates the branch.
2. Each **task** is triggered on its own. Its author commits on the branch the host action
   cut for it and opens nothing.
3. `work-completion.py` commits the run's changes, lands them on the story's branch and closes the task —
   unless the author reported work `remaining`, which leaves it open with the list on it.
4. The **story's** PR accumulates all of it. The maintainer reviews and merges the story as
   a whole.

⚠️ **The story's PR opens when the LAST task completes.** The target experience: trigger the
story, come back to a finished PR carrying the whole story's work. The all-tasks-closed gate lives
in `open-story-pr.py` itself, so the authors-job call and the merge-path net inherit it
identically; every earlier landing just reports how many tasks remain. ⚠️ An unreadable or empty
task list degrades to open-when-ahead with a warning — an early PR is a nuisance, a story that can
never get its PR is lost work.

⚠️ **NO COMMITS IS NOT THE SAME AS UNFINISHED, AND CONFLATING THEM HALTED A STORY.** Some tasks are
**checks** — *"confirm whether any spec document encodes positioning in offline terms"* — and their
correct outcome is that nothing changed. The landing used to treat every no-commit run as not
closed, so a task that had done exactly what it was asked stayed open, never reached Done, and
stopped the cascade. Measured on #1140: the run reported success and #1139's next task was never
dispatched.
⚠️ **The discriminator already existed and was simply not reached.** `remaining` is the author's own
structured statement of whether it finished — `[]` means *"I looked, there is nothing"* — and the
closing logic keys on it thirty lines further down. The empty path returned before it.
⚠️ **AND AN ABSENT HANDOFF IS NOT AN EMPTY `remaining` — the fix's first version collapsed them and
closed a task whose author NEVER RAN.** A setup step failed (the playwright CDN hang), the model
step was *skipped*, the completion gate read skipped as not-failed, and the hook saw a clean tree
plus an empty `HANDOFF` env — parsed it to `{}`, called `remaining` empty, closed #1159 as "nothing
to do" and dispatched the next wave. The handoff contract's own three-states rule names this exact
trap: *no handoff at all means no author ran, or its run died before posting*. The schema forces a
real author to emit `remaining`, so only an **explicit** `[]` closes; absence leaves the task open
with "the author never reported — re-trigger it".
⚠️ **An empty result is now recorded, not inferred from silence.** "Checked, nothing to do" and "the
run did nothing" are indistinguishable to a reader otherwise, which is the shape this package keeps
paying for.
⚠️ An **as-is story** producing no commits still stays open: its PR targets the default branch and
GitHub closes it natively on merge.

⚠️ **A TASK IS CLOSED BY THE LANDING HOOK, NOT BY A KEYWORD.** There is no task PR, so there is no
closing keyword and nothing for GitHub to act on. `work-completion.py` closes the issue once its
commits are on the story branch — and **only** when the author reported no `remaining`, which is
the same signal that used to govern whether the keyword was written. An unfinished task stays open
with its outstanding list posted on it.

⚠️ **The story's PR still needs its keyword**, and that is unchanged: it targets the default branch,
so GitHub closes the story on merge the ordinary way.

⚠️ **A TASK REACHES DONE FROM THE LANDING HOOK, AND NOWHERE ELSE.** `close-merged-work.py` sets
Done from a merged PR, and a task has none — so a task closed while sitting in In Progress forever
until the completion hook emitted `closed` and a scripted step moved it. ⚠️ That step is gated on
`closed`, not on the hook succeeding: a task reporting work `remaining` is deliberately left open,
and marching it to Done would erase the one signal saying it is unfinished.

⚠️ **A LANDED TASK IS DONE. IT DOES NOT REOPEN.** A Tester finding, or a pipeline failure, against
work that has already landed becomes either an **ad-hoc commit on the story branch** or a **new
task** — never a reopened one.

- ⚠️ **This is not bookkeeping.** Trigger order is derived from `(phase, issue number)`, so
  reopening an early number puts that task back *ahead* of ones that have already landed, and the
  next thing anyone triggers is work that is already done. A new task takes the next number and
  sorts where it belongs.
- Nothing is lost by not reopening: every commit is on the one story branch either way, and the
  story's PR is where all of it is reviewed.

⚠️ **A task still open when its story merges is a signal, not a gap.** Nothing closes it
implicitly: it was abandoned, or its PR never landed. An earlier version closed a merged
issue's open children, which hid exactly the case worth seeing.

⚠️ **`pull_request` events run the workflow from the PR's base branch**, so a workflow fix
does not reach an in-flight story until the default branch is merged into it.

## Routing

**A label on an issue is the front door.** Applying it starts a run, and `delegate.py` reads
the issue's state to pick the role. The same label named in a comment does the same. A
`@claude/<role>` handle in a comment names the role outright and skips the inspection — the
way to override a bad guess.

⚠️ **The label does the work; a comment talks about it — but a comment can ASK for work, and the
script cannot tell.** The `@claude` **label** routes to a working role exactly as it always has. A
comment naming `@claude` with no role handle used to settle straight to the conversational role, and
that was right most of the time and expensively wrong the rest: *"@claude I believe this branch
needs to be updated from its base"* is a request, and the role that answered it was structurally
unable to act.

⚠️ **So rule 1b now CONSULTS rather than settles.** It sets `consult`, the delegate-phase custodian
reads the comment, and it answers `claude` for a question or a working role for a request — before
the role jobs gate on the result, which is the only moment the decision can still change what runs.
`claude` stays the fallback, so a failed, skipped or `undecided` interception lands exactly where
the rule used to send it outright.

⚠️ **`consult` IS NOT `defaulted`, and merging them would be wrong both ways.** `defaulted` means
the state that should decide is **missing** — a real gap, worth announcing, and it carries a remedy
the maintainer can apply. `consult` means the script decided as far as state allows and the only
open question is a judgement about a sentence. Nothing is broken, there is nothing to fix on the
issue, and announcing every one would bury the notices that matter. ⚠️ `report-route.py` therefore
stays **silent** on a consultation that changed nothing, and speaks only when the custodian routed
somewhere the script would not have.

⚠️ **This is not a role chaining off another**, which remains forbidden. The maintainer triggered
the run; the router is deciding which role serves that trigger. Nothing starts work nobody asked
for — the difference is that "who should serve this" is now read from the request rather than
assumed from its shape.

⚠️ **An unknown handle lands there too.** `@claude/nonsense` matches no role, so rule 1b catches it
and the root role can say there is no such role — where rule 3 would previously have shaped the
issue as a story instead.

⚠️ **A STORY WITH TASKS IS NEVER AN AUTHOR'S TO WORK — triggering it means START IT.** Rule 4
short-circuits on the `Branch:` line and used to default a missing `Role:` stamp to the
Implementor, so an already-shaped story — a branch named, tasks written, which is exactly what the
Architect produces and what a careful human files — spent an `opus` run producing nothing (#1096,
measured on #1092). ⚠️ **The disqualifying fact was already in hand**: the rule computes `kids` and
spent it entirely on the remedy text, which read *"trigger one of its tasks instead"* while routing
to an author anyway. It now emits `dispatch` and no role, every role job skips on the empty
`roles`, and the first wave starts. ⚠️ **A story with NO tasks still falls through to its stamped
author** — the as-is path — and that bound is what keeps the two cases apart.

⚠️ **A bare `@claude` on a TASK routes to the Custodian, deterministically.** A task's runs happen
from its story, so a human landing on the task itself is there because something did not happen —
presumed stuck, diagnosed rather than re-run. Decidable from structure (a task's Branch line names
another issue's branch), so it is a script rule, not a consultation: the Delegator is for
judgement, not for facts.

⚠️ **The Delegator may answer in the PLURAL** — a `roles` array, in run order, for a request that
genuinely names two deliverables ("fix it and cover it" is an Implementor then a Tester). Each
member is filtered against the allowlist independently: an invalid member is dropped rather than
voiding the answer, and `undecided` is only ever alone. A plural answer gates multiple model steps
in the one authors job, so the roles run in sequence with no extra wiring.

⚠️ **This changes PR follow-ups.** A bare `@claude` on a PR used to run an Implementor; it now
answers. `@claude/implementor` is the way to ask for the work, and it is unchanged.

⚠️ **`trigger_phrase` is the bare `@claude` for that job, and only that job.** The usual warning —
that a bare phrase makes `@claude/architect do X` extract as the slash command `/architect do X` and
kills the run — cannot bite here, because rule 1b only routes to it when no role handle matched.

⚠️ **A handle skips the role decision, not the context.** It still resolves the story — from
the PR's head branch on a PR, from the issue's **Branch** line on an issue. It did neither on
an issue once, so a handled role started with no story and paid turns rediscovering what the
router already had. Resolve it inside the handle branch; do **not** fall through to the
state-based rules, which would re-judge the role and could pick a different one.

⚠️ **Routing is a shell script, never a model.** It is all readable state; the one call that
needs judgement — which author owns a task — is answered once by the Architect and written
into the task as a `Role:` line.

### When the script has to guess

⚠️ **A `defaulted` route means "ask", not "run".** Rules 1-4 decide from state, and where the
state that should decide is missing they fall back to a default rather than stall. That default is
now a **floor**: the router job puts the question to the root role first, and runs the fallback
only if it cannot answer. The choice this adds is not "script or model" — it is "read the issue or
guess", and guessing was the incumbent.

⚠️ **It is a STEP in the router job, and each alternative is ruled out by something already paid
for here:**

| shape | why not |
|---|---|
| a new workflow run | an event created with the workflow token starts no run, by design |
| a job the roles `needs:` | a job needing a **skipped** job reports cancelled — the #430 revert, verbatim |
| a job that `needs:` the router | too late; role jobs gate on the router's outputs and have already started |

A job cannot gate on a step inside itself. It *can* gate on an output that step produced, which is
what makes the step form work where the job form does not.

⚠️ **The step's answer is filtered by an allowlist, not trusted because it matched a schema.** A
shell step accepts a known role and discards anything else, so a malformed answer, a failed step, a
skipped step and `undecided` all arrive as the same thing: the script's default, with its notice
intact. **A failed interception must never mean nothing runs** — degrading to the old behaviour is
the correct failure, and the step carries `continue-on-error` so the job reaches the fallback.

⚠️ **"ALL ARRIVE AS THE SAME THING" IS CORRECT FOR THE ROUTE AND WRONG FOR THE REPORT**, and that
distinction cost the feature. Collapsing every failure to the script's default is the right
*behaviour*; collapsing them in the *log* means "the model declined" and "the model's answer never
arrived" — opposite problems — look identical from outside. Measured: across every `defaulted`
route on record the fallback fired **100%** of the time, the interception model step ran for a real
33s rather than the sub-second dead-run fingerprint, and nothing anywhere recorded which cause it
was. The fallback branch now names it: no output at all, `undecided`, no `role` field, an unknown
role, or a role with no `why`.

⚠️ **AND THE INTERCEPTION MUST SHIP A TRANSCRIPT LIKE EVERY OTHER MODEL STEP.** It was the only one
that did not. A routing decision is the *cheapest* thing to leave unrecorded and the most expensive
to lose: it runs for a second, it decides what the whole rest of the run does, and its output is
consumed by a shell step that keeps nothing. ⚠️ **A decision with no record is worse than a channel
with no reader** — with a dead channel you can at least go and read the producer; here there is
nothing to read, so the only evidence is that the outcome never changed.

⚠️ **`undecided` has to be a real answer, or the schema manufactures a guess.** An enum of roles
alone leaves no way to say "the issue does not tell me", so a model obliged to pick one produces
exactly the confident-wrong route this is meant to remove — and worse than the script's, because
answering suppresses the guess notice that would have flagged it.

⚠️ [E9] **`kind` IS RESOLVED FOR EVERY ISSUE TRIGGER, AND FOR A LONG TIME IT WAS SET ON ONE PATH ONLY.**
Rule 3 — the unshaped-issue path — computed it; rules 1, 2 and 4 emitted empty, which prints as
`n/a`. Nothing read it, so nothing broke, until a workflow guard did: the Architect's dispatch step
tested `kind != 'epic'`, and `'n/a' != 'epic'` is **true**. Measured on #1112 — a maintainer's
comment asking the Architect for a task had that task dispatched to an Implementor a minute later.
⚠️ **The guard worked on the path it was written for and failed on a sibling**: a *label* trigger
routes through rule 3 and resolves `epic` correctly, which is what made it look proven. A *handle*
reaches the same job through rule 1.
⚠️ It belongs with the story and the branch for the same reason they do — **read from state, never
in doubt.** A handle short-circuits the ROLE decision; it must not also cost the run a fact nobody
was judging.
⚠️ **AND A GUARD THAT STARTS WORK MUST FAIL CLOSED.** Written negatively, an unresolved kind
dispatched. Written positively — only a kind recognised as workable proceeds — an unknown one
cannot. That also survives `team.kind()` falling back to `story` on a failed API call, which the
negative form could not.

⚠️ **It decides the ROLE and nothing else.** The story, its branch and the issue kind stay on the
script's outputs. They are read from state and are not in doubt; letting a model restate them puts
two sources on one fact.

⚠️ **Announcing a default belongs AFTER the decision, not inside `delegate.py`.** It was inside,
and that was one step too early: the script announced its guess before anything had been asked, so
an intercepted run posted "I guessed" and then ran something else — a notice describing a decision
that never took effect, which is worse than none because it is a false record of *why* the run did
what it did. `report-route.py` runs after resolution and says whichever actually happened.

⚠️ **Deciding correctly does not repair the issue.** The missing stamp is still missing and the
next trigger takes the same detour, so the remedy is carried on **both** outcomes. Only the
sentence changes: a guess "keeps guessing the same way", an interception "costs a run before any
of the work starts".

⚠️ **The role stamp is a record, not a route.** Roles stamp `@claude/<role>` as they start,
so the labels read as "these agents have been here". Nothing routes off them.

⚠️ **`@claude` IS SPENT AT CLOSE — the closing hook swaps it for `@claude/complete`.** On an open
issue the front-door label means *in flight*, and that meaning is load-bearing: `dispatch-next.py`
skips any open task carrying it, so a stale one blocks the cascade **forever** (#1108 found six).
The hooks keep the marker accurate by swapping it wherever work completes: both of
`work-completion.py`'s close paths, and **every** issue on `close-merged-work.py`'s merge path —
the merge path deliberately swaps issues it did not itself close, because a story's own issue is
closed *natively* by GitHub when its PR merges and no hook ever touches it.
- ⚠️ The swap fires no workflow run: hook label edits use `GITHUB_TOKEN`, whose events start no
  runs — the third loop guard, working as intended.
- ⚠️ `@claude/complete` must exist in the repo, like every other label the hooks apply.
- ⚠️ A stale `@claude` on an open issue that predates the swap is a **hand-removal** — removing it
  re-arms the issue as dispatchable, which is exactly why no sweep does it automatically.
- The `@claude/<role>` stamps are untouched: they are the record of what ran, not a marker.

⚠️ **A CASCADE MUST BE ADMITTED BY EVERY ACTOR GUARD, NOT JUST THIS PACKAGE'S.** Dispatching by
App means every cascaded run is authored by a bot, and the host action carries its own human-actor
check that refuses **at setup** — before the model is called and before any hook here runs.
Admitting the App in the workflow's own `if:` only gets the job started. A consuming repo must
also name it in the action's `allowed_bots`, and name it **explicitly** rather than allowing all
bots: the action's warning is that a wildcard lets any external App invoke it with a prompt it
controls. ⚠️ It is a **setup** failure, so there is no result payload and `num_turns` cannot
diagnose it — read the failing step instead.

⚠️ **Guard the loop.** Every stamp is another `labeled` event. Gate the trigger on the label
name being *exactly* the front-door label, and exclude bot actors. Both hold independently.
(A third guard comes free: a stamp applied with `GITHUB_TOKEN` does not start a workflow run
at all.)

## Roles

| role | picked up from | writes |
|---|---|---|
| `@claude` | its name in a **comment**, with no role handle; **and** a route the script had to guess | an answer, a role name, and repairs to process state. No code, no branch, no PR — it is who you talk to |
| Architect | an epic or an unshaped story | the issue, a story's branch, and its tasks |
| Researcher | a spike | findings and a recommendation, appended to the issue by a hook — it holds no shell |
| Implementor | a task stamped `Role: implementor` | code, outside the design system |
| Designer | a task stamped `Role: designer` | code, inside the design system |
| Tester | a task stamped `Role: tester`, one per story | tests |
| Writer | a task stamped `Role: writer`, one per story, run **first** | the product specification, then human-facing documentation — **never** a `CLAUDE.md`, `AGENTS.md`, `.claude/**` or `.claude-team/**` |
| Security | every merge, plus its handle on a PR | issues it files |

### The custodian's repair remit

The root role is the only one that may put **process state** right — the breakage no role owns,
which is exactly why it accumulates: an issue off the board, a child never parented, a missing
classification label.

⚠️ [E3] **It names repairs; a hook applies them.** The model returns JSON, `apply-repairs.py` acts on it,
and the hook's repertoire is a fixed enum — `board-item`, `sub-issue-link`, `classification-label`.
That is what makes "never touches content" a fact about what *exists* rather than a promise in a
prompt, which was the acceptance criterion: enforced by what the role can **reach**.

⚠️ **Its tools are allowlisted by SUBCOMMAND**, the same way Security's are and for the same reason:
`Bash(gh:*)` includes `gh issue edit --body`, which rewrites an issue, and a family grant cannot
express "read but do not write". ⚠️ `gh api` is deliberately absent — it reaches every endpoint the
token has. Relationships survive that narrowing because `gh issue view` exposes `parent`,
`subIssues` and `subIssuesSummary`; **that was checked before narrowing**, because Security already
taught this package that too narrow starves a role *silently*.

⚠️ **The Custodian holds DIRECT GIT and `contents: write`, by the maintainer's decision** (spec
OQ-5 on the workflow spec): branch management is part of its remit, granted whole for convenience.
The earlier posture — `contents: read` as the structural guarantee that this role touches no
content — is superseded. What remains structural: it holds no `Write`/`Edit`, so it can move refs
but has nothing of its own to commit; `github_token` is passed, so the job's `permissions:` block
is what its token actually gets; and every run's transcript is captured, which is the audit for
the bound that is now instructed rather than enforced.

⚠️ [E12] **Fix AND report, never fix quietly**, and this is the rule most likely to be eroded by a
well-meaning change. Every repair appends to one log comment on its target carrying *what was
wrong* and *why*. The value of this system has come from breakage being visible: a 404 nobody hid
is what produced the rule that prevents it, and a custodian that had silently created the branch
would have left a working run and a rule still wrong, with nobody knowing to fix it.

⚠️ **A repeat escalates instead of repairing.** Reaching for the same `kind` on the same target
twice means the cause was never fixed, so the hook withholds the repair, files an issue, and leaves
the instance broken **on purpose**. A custodian quietly repairing the same thing weekly has become
a suppressor of the signal that would have fixed it properly. The check reads the log comment —
state on the issue, not a memory of the last run.

⚠️ **`unrepairable` is the other half and carries the weight.** Anything outside the enum, anything
needing content changed, and anything whose real fix is upstream in a rule goes there with what
would fix it. Keeping it separate from `repairs` is the point: a custodian that quietly fixed
everything would erase the evidence that the rule is wrong.

⚠️ [E4] **AND IT HAS TO REACH THE ISSUE, WHICH FOR A LONG TIME IT DID NOT.** `apply-repairs.py` posted
`repairs` as a comment and `print`ed `unrepairable` to the job log — so the half that carries the
weight reached nobody. That is the **fifth** instance of this exact shape here, after `DEFAULTED`,
the author handoff appended in a job its readers never run in, `decisions` on the PR path, and
`docsCandidates`: a required output with no consumer, shipped and believed to work.

⚠️ **The user-visible symptom was the custodian looking unhelpful.** A run identified a stale task
title and named the role that should rename it — a perfectly good redirect, written to a job log.
From outside, the role had said "not my job" and offered nothing, which is exactly the complaint
the design was meant to answer. **A role that answers into a channel nobody reads has not
answered.**

⚠️ **It reports on the TRIGGER, because a finding carries no target of its own** — the schema gives
it `what` and `wouldFix`, deliberately, since most findings are about a rule rather than an issue.
So the hook needs the triggering issue *or* PR; the root role answers on both, and each workflow
expression blanks for the other. ⚠️ Commenting on a PR needs `pull-requests: write`, not
`issues: write` — the endpoint reads as `issues` and the permission checked is not.

⚠️ **Same comment marker as the repairs, and it APPENDS.** One marker so everything the custodian
has done to an issue reads as one history, with the section prefix — `⚠️ **Not repaired**` — as the
only thing distinguishing it, so "I did not fix this" can never be misread as "I fixed this".
Appending rather than upserting matches `repairs` and is load-bearing for the same reason a repeat
repair escalates: **a finding that recurs is the signal that its cause is still there**, and an
upsert would erase it.

⚠️ **The answer still goes in the tracking comment.** With `--json-schema` the final message is
JSON, so `track_progress: true` stops being cosmetic and becomes the only place a human reads a
reply — a run that answers into the JSON and leaves the comment empty has answered nobody.

⚠️ **The root role has three jobs and two prompts.** `claude.md` is the conversation — someone asked
it something. `route.md` is the interception — nobody asked it anything, and its whole output is a
role name plus the reason, returned as JSON to a shell step. Splitting them is not tidiness: a
conversational prompt handed a routing decision answers in prose, and a routing prompt handed a
question answers with an enum. Same persona, same bounds, different contract.

⚠️ **`route.md` is loaded by a STEP, so it runs in agent mode**, and that is the one place here
where losing the tag-mode tracking comment is the *better* outcome — the durable record is the
comment `report-route.py` writes, and a tracking comment beside it would be two comments for one
sub-second decision. It is also why the prompt is authoritative rather than wrapped in the
framing that tells a model its instructions are the triggering comment; there is no comment on a
label event to be confused by. ⚠️ `structured_output` is set after the run in either mode, so the
schema still binds — checked in the action's source, not assumed.

⚠️ **The Researcher answers; it does not shape.** It appends findings to the spike and stops —
it creates no story, cuts no branch and starts no author. The maintainer decides, and only then
is there something for the Architect to shape. A research run that quietly starts building has
committed to an answer nobody approved.

⚠️ **It appends to the issue and never rewrites the question**, for the same reason the Architect
must not rewrite a bug report, inverted: there the body is an investigation that already
happened, here it is the question itself. The maintainer's framing carries which options they
already weighed and which constraint they called non-negotiable, and replacing it destroys the
thing that was asked.

⚠️ **A SHELL IS NOT THE DIVIDING LINE BETWEEN ROLES — INPUT PROVENANCE IS.** Every authoring role
has one, the Writer included: a specification says what a brewer can do and see, which means
starting the app and driving it, not reading the source. Withholding `npm`/`npx` from the Writer
made the one role that owns the spec unable to produce it, and it failed the expensive way — by
burning turns on permission denials rather than saying so.

⚠️ **AND THE SHELL THEY DO HOLD IS THE CONSUMER'S TO NAME, WHICH THIS FILE USED TO DO ITSELF.**
Every authoring role was granted `Bash(npm|npx|node:*)` and nothing else, so an author in a
Python-gated repo could not run the gate at all — **including in this repo**, whose own gate is
`python3 -m unittest`. It is a straight violation of the invariant at the top: *nothing here names
a consuming repo, its branches, its gate or its packages.* A toolchain is the same category as a
gate.
⚠️ **The symptom is a role that produces a change it cannot verify**, and reports that in a
section easy to skip. Measured on run 32561656056: the Implementor reimplemented its assertion in
`node` against the real data and said plainly, in its 🔔 Maintainer block, that this was not the
Python suite running (#46). It is milder here, where a maintainer reads the handoff, than in a
consumer where nobody does before merging. ⚠️ It silently changes what the **Tester** means too —
a Tester that cannot execute the suite it just wrote is asserting that its tests *should* pass,
which is the derive-from-the-implementation failure wearing a different hat.
⚠️ **A `runtimes` input replaces it**, defaulting to `npm,npx,node` so no existing consumer
changes behaviour, each entry expanded into a `Bash(<name>:*)` grant by a step in the authors job.
⚠️ **The value is SANITISED, not interpolated raw** — it lands inside the quoted `--allowedTools`
string, which the action parses line by line, so an entry carrying a quote could rewrite the flags
after it. A consumer already controls its own caller workflow, so this is not a privilege boundary;
it is what stops a typo widening the grant instead of failing. ⚠️ **Resolving to nothing fails the
step**, because an author with no runtime cannot run any gate and the silence is the whole defect.
⚠️ **`Bash(*)` was never available as the fix.** The Researcher's own history records that a broad
grant shipped briefly and was a live token-exfiltration path: the action re-injects `GH_TOKEN` and
`CLAUDE_CODE_OAUTH_TOKEN` into the agent's environment whatever the step declares.
⚠️ **The four authors now share ONE grant, so the Tester gained `node`** — a stated widening, not
a side-effect. It held `npm`/`npx` and not `node` with nothing anywhere saying why, and `npx`
already executes node code, so the omission bounded nothing. Per-role runtime lists were the
alternative and would make a Python consumer configure four of them.
⚠️ **The narrow roles are untouched and must stay so**: the Researcher holds no shell by design,
and the Custodian and Security are allowlisted by subcommand. `runtimes` is for the authoring
roles alone.
⚠️ **One toolchain name survives, deliberately unfixed:** Security still holds `Bash(npm audit:*)`.
That is a dependency-audit capability rather than a gate, so it is a different question — but it is
the same category of assumption and should be named when someone settles it.

⚠️ **It is the only role that reads the open web, and the only one whose input the maintainer did
not write** — which is exactly why **it holds no shell**. No `Bash` of any kind, no `Write`, no
`npm ci`, no build. It reads (`Read`/`Glob`/`Grep`), it fetches, and it returns JSON.

⚠️ **Taking the secret away instead is not available, and that was the first fix attempted.**
`claude-code-action` re-injects it whatever the workflow step declares —
`src/entrypoints/run.ts` sets `process.env.GITHUB_TOKEN` and `GH_TOKEN`, and
`base-action/src/parse-sdk-options.ts` hands the agent `{...process.env}` — so `GH_TOKEN` **and
`CLAUDE_CODE_OAUTH_TOKEN`**, an account credential rather than a repo-scoped one, are readable by
anything the agent can execute. The credential cannot be removed; the ability to read it can.
⚠️ Narrowing rather than removing would not have held either: `Write` plus any runner is
agent-authored code, so a probe spec *is* arbitrary execution. That is why probing was dropped
from this role and a measurement it needs becomes someone else's task (#665).

⚠️ **A credential can reach the agent through a FILE, not only through the environment**, and
removing the shell does nothing about that. `actions/checkout` defaults to
`persist-credentials: true`, which writes the token into `.git/config` as an
`http.<host>.extraheader` — so a role holding nothing but `Read` can recover it and post it
anywhere it can fetch. A web-reading role's checkout therefore needs `persist-credentials: false`.
⚠️ Only the reading role's: an authoring job pushes, and disabling it there breaks the push.

⚠️ **`WebFetch` is itself an egress channel**, so a narrower `Bash` grant was never the fix —
exfiltration needs no shell if the agent can be induced to fetch a URL. Only the absence of a way
to *read* the environment closes it.

⚠️ **It carries no `id-token` and passes its own `github_token`, and those two are one change.**
Removing the permission alone broke the role outright — `setupGitHubToken()` mints an OIDC token
and exchanges it for a GitHub App token, so with no OIDC and no supplied token the action cannot
authenticate at all (#668). Passing `github_token` short-circuits that path before OIDC is
reached.

⚠️ **And it is what makes a `permissions:` block mean anything to the agent.** That block scopes
`secrets.GITHUB_TOKEN`. It does **not** scope the App token the exchange mints — those grants come
from the service — and `run.ts` puts whichever token it obtained into `process.env.GH_TOKEN`. So
without the input, a job's `permissions:` bounds its *hooks* and not its *model*, which is exactly
backwards: the hooks are the trusted half. ⚠️ **Every other role still takes the App-token path**,
so their blocks do not bound their agents either. Smaller problem — their input is maintainer-
shaped issues — but not zero, and not what those blocks look like they say.

⚠️ **The residual, written down rather than claimed away:** the action's base allowlist unions in
`Bash(git add|commit|rm:*)` and `git-push.sh`, and a role cannot remove them. Two things neuter
them, and the order matters: there is no `Write`, so the agent cannot author a file worth
committing; and `contents: read` bounds the token — **but only because `github_token` is passed**.
That second half was stated without its caveat once, and it was wrong about which token it
described.

⚠️ **A spike that reports only what it settled is not finished.** What it could *not* determine is
the section under the most pressure to skip and the most valuable to keep — without it the next
person re-derives the gap without knowing it was one.

⚠️ **Implementor and Designer split on the package a change touches, not on judgement**, so
the boundary can be checked rather than negotiated.

⚠️ **But the Designer repairs the consumers its own change breaks**, and that is not a hole in the
boundary — it is what makes the boundary survivable. A primitive is an API, so changing one can
stop its consumers compiling, and the same role is told to hand over a green gate. Those were
contradictory instructions and a run had to disobey one of them silently. The licence is bounded
by a checkable line: **repair what your change broke, never what was already broken**, and keep it
mechanical. A consumer needing a *different value* rather than the same value spelled differently
is a behavioural decision, still the Implementor's, and still a stop-and-report.

⚠️ **A task spanning both is two tasks only when the consumer half is behavioural.** Splitting a
change whose consumer side is purely keeping the build green makes every primitive rename two
tasks and a stall.

⚠️ **The Tester and Writer are tasks the Architect cuts** — the Writer ahead of the authoring
tasks, the Tester after them. ⚠️ **The maintainer triggers the STORY; automation extends inside
it** — a landed-and-closed task dispatches the next via an App-minted issues:write token adding
the same `@claude` label a human would. The label doubles as the in-flight marker (`labeled` only
fires on an actual add), so a failed or unfinished task halts its wave rather than looping, and
absent secrets leave the cascade dark with the manual gesture untouched.

⚠️ **A test derived from the implementation is worthless, and looks exactly like coverage.**
It asserts what the code does, so it passes by construction and cannot fail for the only
reason worth catching. The Tester derives from *expected* behaviour — the **product
specification** first, then the story's outcome, the `testingNotes`, the acceptance criteria —
and may read a component for one thing only: how to **address** an element. Knowing how to
click a thing is not knowing what it should do.

⚠️ **The specification is the only one of those that outlives its story.** The other three
describe a single change and are gone once it merges, which is precisely when a regression
suite needs to know what the product promises — so without a specification the derive-from-
behaviour rule silently inverted for everything except the story in front of you. The Tester
cites behaviour ids in its plan, which is what makes coverage a question a reviewer can ask
rather than a claim they have to accept.

⚠️ **A failing test is a finding, not a chore.** It is filed on the authoring task, carried in
the Tester's own report, and left failing. Weakening or deleting it to get green converts a
finding into nothing, and a green suite that got there by deletion is worse than a red one.

⚠️ **THE WRITER DOES NOT OWN THE AGENT INSTRUCTIONS, AND THIS FILE USED TO SAY IT DID.** Every
`CLAUDE.md`, every `AGENTS.md`, everything under `.claude/` or `.claude-team/` — the role prompts
included — is out of the Writer's scope, and out of every role's. It was a maintainer's decision
to grant it and a maintainer's decision to reverse it.
⚠️ **The reason is not tidiness.** Those files are the instructions the roles run on, the Writer's
own among them. A role editing them rewrites its own operating rules and its peers', inside a
story PR being reviewed for something else — so the change that governs every future run arrives
as the least-examined part of the diff. Ordinary documentation is checked by whether it reads
true; an instruction change is only checked by what it makes agents do next time, which nobody
sees until it has already happened.
⚠️ **A prohibition with no outlet turns a finding into silence**, so the Writer reports a stale or
wrong instruction in its 🔔 Maintainer section with the file, what is wrong, and what it would
change it to. A precise report is worth more than an unreviewed edit.
⚠️ **It is pinned in BOTH places it was written**, the prompt and the workflow's job header.
Correcting one and leaving the other saying the opposite is how the claim returns — the comment
is what the next person editing that job reads.
⚠️ **The original reason for splitting the Writer out survives the reversal**: `CLAUDE.md` was the
single biggest source of merge conflicts because every role edited it. Nobody editing it is a
stricter answer than one role editing it, so the conflict argument is satisfied either way.
⚠️ **The prompt is the only enforcement today**, which by this file's own standard is the second
line of defence and not the first. A deterministic guard — a run refusing to commit changes under
those paths — is the structural version, and it collides with **this** repo, whose product *is*
those files. That is filed rather than guessed at.

⚠️ **The Writer owns the product specification, and that is why it runs FIRST.** A
specification is only worth anything if it says what the code *should* do, and it cannot say
that if it was written by reading the code that already exists — a consumer deriving from such
a document is deriving from the implementation at one remove, with the rule against it looking
satisfied. Ordering the Writer ahead of the authors makes "from intent, not from the diff" true
by construction rather than by instruction, and hands the authors a sharper brief besides.

⚠️ **Its task is cut on every story THAT DIVIDES, and inside that scope it is unconditional;
the Tester's is judged.** Every story changes what the product does, so there is always something
to specify. Before the spec existed the argument was weaker — the Architect could not predict
`docsCandidates`, and asked to guess it answered "no" every time: across every story before that
rule, not one Writer task was ever cut.

⚠️ **THE UNSCOPED WORDING CONTRADICTED THE DON'T-SPLIT RULE, AND BOTH WERE ABSOLUTE.** *"A story
one author can finish should not be split"* against *"a `Role: writer` task on EVERY story,
Always — not a judgement call"*: a Writer task **is** a task, so obeying the second made the
first unreachable, with no precedence stated anywhere. A run had to disobey one silently, and
did (#47).
⚠️ **The scope is the fix; softening the rule is not.** *"Cut one where it seems needed"* reverts
to precisely the failure that produced the rule. What changed is **which decision the Architect
is making**: the size question in step 4, which it was making anyway — not "does this deserve a
spec", which it has answered wrong every time it was asked.
⚠️ **The discriminator is stated rather than left to feel:** *does a specification need writing
before the code?* If yes, the story divides and the Writer task is cut first. Ambiguity resolves
to **divide** — an unnecessary Writer run is one cheap run reporting nothing to specify, and a
skipped necessary one is a story shipping with nothing saying what the product now promises.

⚠️ **Running first strands `docsCandidates`, and that must be handled rather than left.** The
authors emit them after the Writer has finished, so nothing consumes them in the same story — a
channel with no reader, which is the shape that shipped dead twice here. They stay on the
story's issue, and the maintainer re-triggers `@claude/writer` on the same task once the authors
land. The Writer's own prompt tells it to say whether it expects to be needed again, because it
is the only party positioned to know.

⚠️ **Per story, not per epic** — for the Writer too. An epic-wide documentation pass sounds
cheaper, and its usual justification is that one branch touching the docs avoids conflicts.
That only holds if stories land in parallel; where they merge one at a time, a later story
already carries the previous one's docs, and deferring only moves the explanation further
from the change it explains.

⚠️ **Trigger order is derived, never stamped.** Tasks sort by `(phase, issue number)`: phase
from the `Role:` stamp — the writer, then the authors, then the tester — and number within a
phase, because
the Architect creates them in the order it intends. A task is ready once everything before it
is closed, so the first open task is the one to trigger. Both inputs are things the Architect
must produce for other reasons; a third stamp naming an order would be a third line it could
skip.

## The handoff between authors

An author's step carries `--json-schema`, so its final message is a contract: `remaining` for
whether the task is finished at all, `decisions` for the record, `testingNotes` for the Tester, `docsCandidates` for the Writer. A hook posts it to
the **story's issue** as one comment per task, where the Tester reads it on its own trigger. ⚠️ The Writer reads it only
on a **re-trigger** — it runs before the authors, so on its first pass the comments do not exist
yet.

- ⚠️ **Both keys are required and `[]` is a real answer** — "I looked, there is nothing",
  which a consumer can act on. A missing key says nothing at all. That distinction is the
  entire reason this is a schema and not a prose section.
- ⚠️ **The story's issue, not its PR.** The PR does not exist until the last task completes,
  so a handoff written during any earlier task would have nowhere to go.
- ⚠️ **A PR follow-up must reach the story too, and for a long time it did not.** The workflow
  blanks `ISSUE` on a PR trigger and the hook returned on that alone — before ever reading
  `STORY`, which `delegate.py` rule 2 had already resolved from the head branch. So the one run
  that carries **review feedback** produced a schema-forced handoff and dropped it. A `PR` env
  var is the other half of the same trigger; without it `decisions` has no path on the only
  trigger it exists for.
- ⚠️ **`remaining` is the only way an author can say it did not finish, and leaving the closing
  keyword out of the PR body was never one.** `finish-pr.py` put it back — it asked whether the
  keyword was present, never why it was absent — so the omission an author meant as a signal was
  overwritten and the task closed as **completed**. Measured: #617's wiring was never written, it
  closed anyway, and the Tester that ran next found no feature to test. The keyword is now
  withheld when `remaining` is non-empty, the PR carries a warning block saying so, and the task
  gets a comment listing what is left.
- ⚠️ **The schema beats the prose, deliberately.** A body is something a model can write anything
  into, including a closing keyword contradicting its own report — so a non-empty `remaining`
  **strips** the keyword rather than warning about the contradiction and letting the task close.
  The forced channel wins over the skippable one; that is the whole reason there is a schema.
- ⚠️ **The withheld keyword becomes a bare `#N` reference, not nothing.** That keeps the PR
  discoverable from the task while leaving `closingIssuesReferences` empty, so
  `close-merged-work.py` finds nothing to close by either of its two routes. ⚠️ Its fallback is a
  regex over the body, so the warning block's own wording must never read as a closing keyword —
  asserted, because "does not close #N" in the wrong phrasing would silently re-close the task the
  block exists to keep open.
- ⚠️ **`remaining` is upserted on the task; `decisions` is appended to the story.** Not an
  inconsistency: what is left is a snapshot that a later run supersedes, while a decision is a
  record that a later run must not erase.
- ⚠️ **`decisions` is the antidote to a review that dies in its own thread.** A maintainer
  changes course on a PR; the issue still describes what they rejected, and nothing rewrites it.
  The next agent reads the old plan and rebuilds the rejected thing — measured: a resolver
  deleted on review (#626) was reinstated two PRs later (#651) by an agent reading a story that
  still asked for it, and its author had done everything right, including leaving two 🔔
  Maintainer heads-ups that nobody picked up. **A PR comment is not a durable artifact.** The
  issue, the spec and the code are, and a decision reached in review lands in none of them
  unless something puts it there.
- ⚠️ [E6] **The decisions log APPENDS; every other hook comment upserts.** That difference is
  deliberate, not an inconsistency. A status board or a handoff is *derived* — regenerated whole
  each run, so replacing it loses nothing. A decision is a **record**: a PR draws several rounds
  of review, and round two replacing round one destroys the fact the comment exists to keep. It
  is still one comment; rounds stack inside it.
- ⚠️ **Reporting a decision does not discharge it.** `decisions` records what changed; it does
  not correct the specification, the acceptance criteria or the sibling task that now read the
  old way. `supersedes` names them precisely so a human can go and fix them — a role reporting
  a decision should also raise it where the maintainer will act on it.
- ⚠️ **Deterministic at both ends:** the schema forces the author to produce it, the hook
  forces delivery. Neither is a model instruction. Asking a model to leave a
  machine-readable block for a later role is the version that fails.
- A candidate is a proposal, never an order. Rejecting all of them is a correct outcome.
- ⚠️ [E5] **Three states, not two.** Entries mean the author found something; `[]` means it looked
  and found nothing; **no handoff comment at all** means no author ran, or its run failed
  before posting. A consumer that collapses the last two will treat a failed run as a clean
  one.
- `docsCandidates[].file` is a **free string**, never an enum of a repo's paths — these roles
  are portable and must not encode one repository's layout.

⚠️ **The transport is the half that breaks, not the schema.** It was first appended to the
consuming roles' prompts from the same job — which only works if those roles run in that job.
They do not, so nothing ever received it and the feature shipped dead. A comment outlives its
run; a step output does not.

⚠️ **`--json-schema` takes inline JSON, not a path.** The schema is a file in this package, so
a workflow step has to compact it to one line and inject it. Two hazards worth asserting
rather than discovering: the value is wrapped in single quotes, so the file must contain none,
and the argument list is parsed line by line, so it must stay on one line.

## Prompt composition

A role's prompt is `prompts/_shared.md` then `prompts/<role>.md` from this package, followed
by the consumer's overlay in the same order. The base says how the role behaves and how the
hierarchy works; the overlay says what the repo's gate is, where its code lives, and any
house rules.

⚠️ **The prompt forbids planning-and-stopping, not just stating an intention**, and the two are
easy to conflate. The observed failure is never a sentence saying "I'll get to it" — it is a
**tidy checklist with the boxes unticked**, which reads as progress at a glance. Measured twice
(#834, #866): ~6 turns, ~30s, a good plan, nothing done, run reports success.

⚠️ **THE UNTICKED CHECKLIST IS THE SYMPTOM; BACKGROUNDING IS THE CAUSE.** This was documented for
a long time as a model that plans and then idles, which is what it looks like from the comment. A
captured transcript (#1018) shows otherwise: the model launched a **background subagent**, called a
**schedule-a-wake-up** tool to wait for it, and signed off with *"I'll wait for the research agent
to complete."* 7 turns, 24s, `is_error: false`, `subtype: success`, nothing written. The boxes are
unticked because the work was **delegated to a continuation that never comes**, not because nothing
was attempted.

⚠️ **"Both completed on a plain re-trigger, so nothing was blocking them" was the wrong inference
from a true observation.** Re-triggering works because the failure is **nondeterministic** — it
depends on whether the model reaches for the background tool at all. That is a coin flip, and
reading it as "nothing was wrong" is what kept the real mechanism hidden across three runs.

⚠️ [E16] **The fix is the prompt, and it has to be specific, because the general rule did not bind.**
"Never end a run with an intention" was already there and the model did not think it was ending on
one — it believed it had *scheduled a resumption*, and the tool call had returned success. The rule
therefore names the behaviour (backgrounding) rather than the feeling (giving up), and it must
preserve synchronous delegation: a subagent invoked in-turn returns its result and works correctly.
⚠️ **Forbidding delegation outright would be the wrong fix** — it removes a useful capability to
correct a default.

⚠️ **A denylist is not available as the fix, and that is a finding in itself.** The tools involved
were in **neither** the role's `--allowedTools` **nor** the action's base set, and executed anyway.
An allowlist that does not bind cannot be tightened into a denylist that does; the prompt is the
only lever the consuming repo actually holds.

⚠️ **The host action's own scaffolding contributes**, which is why the prompt has to push back
explicitly. Tag mode asks the model to keep a todo list in its tracking comment; writing that list
is a real, satisfying, visible action, and it is the one thing both stalled runs accomplished.

⚠️ **AND THE PROMPT NOW GUARDS BOTH ENDS, WHICH IT DID NOT.** Everything above concerns stopping
too early; a role can also stop too **late**, and that costs more — it produces nothing *and*
explains nothing. Measured on a Writer run: 81 turns, the target screen driven and read by roughly
turn 35, not one line of the deliverable written when the cap hit. ⚠️ **The two halves read as a
contradiction unless the discriminator is stated**, and it is non-convergence rather than
difficulty: attacking the same obstacle with variations rather than steps forward is the signal to
bank and report. ⚠️ **Stopping is not permission to invent** — that is the failure the stop exists
to avoid, and it is worse than either, because nothing about it looks wrong. ⚠️ **And no issue body
can require a role to spend the whole budget**: an unmeetable acceptance criterion is a finding.
An issue that removes a role's permission to stop converts a cheap, informative failure into an
expensive, opaque one — measured across five runs on one story, where the first three reported
precisely what blocked them in 1–4 minutes and the last two ground to the cap with nothing.

⚠️ [E15] **AND THE THIRD SHAPE IS GATHERING WITHOUT PRODUCING, which neither of the other two catches.**
Stopping early is a plan with unticked boxes; stopping late is grinding on one obstacle. This is
neither: every turn succeeds, every turn yields something genuinely new, and the deliverable is
still empty when the budget ends. Measured on #746 — **17 driver scripts, 20 screenshots, 81 turns,
no specification**. Nothing was blocked and nothing was repeated, so the non-convergence
discriminator never fired. ⚠️ **The check has to be the deliverable, not the sense of progress**:
"what is in the file I was asked to produce" rather than "am I learning things".

⚠️ **AN ISSUE'S WORKED EXAMPLE OUTRANKED A STANDING RULE, AND THAT ORDERING IS NOW STATED.** #746's
body carried a `chromium.launch(...)` snippet from before the harness convention existed, and the
run followed it 17 times on a prompt that said to use the repo's own harness. An issue says *what*
to deliver and ages in place; a rule about *how to work* is newer and wins — and the role is told
to flag the stale example so it stops costing runs. ⚠️ This is the general hazard of putting
technique in an issue body: the issue cannot know what changed after it was written.

⚠️ **"Confirm scope" is the tell.** A plan step whose natural completion is asking a human has
planned its own failure — nobody is reading while a run executes. The prompt says ambiguity is not
a stop condition: choose a defensible reading, ship, and raise the question in the 🔔 Maintainer
section.

⚠️ [E17] **The prompt is the second line of defence, not the first.** The custodial phase fails the run
when the deliverable is missing, because for as long as this went unnoticed it reported success.
Neither replaces the other: the check is how anyone finds out, the prompt is what stops it.

⚠️ **Shared first, and that ordering is load-bearing.** `_shared.md` opens by overriding the
host action's own prompt, which for comment events states repeatedly that the model's
instructions are the triggering comment. Ours arrives after all of that, so the override has
to be the first thing in it.

⚠️ [E18] **Keep the split honest.** A rule that would be true in any repo belongs in the base; a
rule that names a command, a path or a package belongs in the overlay.

⚠️ **`trigger_phrase` must be the role's exact handle.** It gates nothing when a prompt is
supplied, but the action extracts everything *after* it as "the user request" and yields
that as the final content block, which the CLI scans for a slash command. Set to a bare
front-door label, `@claude/<role> do X` extracts as `/<role> do X` and is swallowed as an
unknown slash command — the run reports success having never called the model.

## Hooks

Deterministic steps that run around each model step, so backlog bookkeeping cannot be
forgotten by a model that ran out of turns or simply skipped it.

| hook | when | does |
|---|---|---|
| `acknowledge.py` | the router job, first | reacts 👀 so the trigger is visibly received |
| `delegate.py` | the router job | picks the role from issue state — routing is scripted, not judged |
| `report-route.py` | the router job, last | says on the issue that this run did not route from state alone — whether the script guessed or the root role was asked |
| `labels-and-status.py` | around every run | one hook, three modes — `stamp`: `@claude/<role>` on the trigger; `kind`: the classification label (`INCLUDE_SUB_ISSUES` reaches the tasks); `status`: board place + Status (column and flags are inputs) |
| `branch-navigation.py` | post, Architect (after `file-sub-issues.py`) + Researcher; **pre, authors** | one decision at every site: task case creates the missing story branch (the #744 net); story case creates only when the story **has tasks**; epic and spike have none, said rather than warned; an existing branch is never touched, and creation appends the compare link |
| `file-sub-issues.py` | post, Architect | parents stories to their epic, tasks to their story |
| `work-completion.py` | post, authors | commits the run's changes (message from the handoff's `commitMessage`), lands them on the story's branch — reconciling a rejected push by merge — and closes the task; a **conflicted** merge fails the step with `unlandable=true` |
| `capture-failure.py` | post, authors — only when a model step failed or the landing conflicted | pushes the run's changes to `failure/<task#>-<run#>-<attempt>` and appends a recovery report on the issue; never fails, never masks the real error |
| `dispatch-next.py` | post, authors when the landing **closed** the task; **post, Architect** (after the branch exists); **in `delegate`** when an already-shaped story is triggered | reads the story's `### Sequencing` section (derived order without one), and adds `@claude` to every open, unlabelled task in the earliest incomplete wave — the cascade, dark when the App secrets are absent |
| `finish-pr.py` | post, authors | the net behind `open-story-pr.py` on the as-is path — labels the PR and reconciles the closing keyword with `remaining`. Returns immediately for a task, which has no PR. ⚠️ Also the net under **stranded commits**: a run that committed with nowhere to land gets its branch **pushed** and a PR opened, and **fails the run** if either step cannot happen — pushing first is what makes the recovery real, since `gh pr create --head` needs the branch on the remote and the runner dies moments later (#13). ⚠️ Reads `LANDED_REF` to tell a landing from a loss |
| `apply-repairs.py` | post, the root role | applies the process repairs it named, records each with what was wrong and why, **reports what it would not fix onto the trigger**, and files an issue rather than repairing the same thing twice |
| `post-findings.py` | post, Researcher | renders its schema-forced findings onto the spike — the role has no shell, so this is the only way they reach anyone |
| `post-handoff.py` | post, authors | posts the JSON handoff to the story's issue, and appends its `decisions` to one running log there |
| `log-to-story.py` | post, Architect + authors + on merge | rewrites one comment on the story listing its tasks in trigger order |
| `log-to-epic.py` | post, authors | rewrites one rolling work-log comment on the epic |
| `open-story-pr.py` | **on merge** | opens the story's PR once a task has landed on its branch |
| `close-merged-work.py` | on merge | closes the PR's issues and files them on the board |
| `custodial-sweep.py` | **post, every role** (`deliverable`) and **on merge** (`branches`) | checks what a run left behind: an Architect with no `Branch:` line fails the run; a story branch that is 0-ahead with a closed issue is deleted |

⚠️ These were prompt instructions until a model skipped them. A scripted step costs no
turns and cannot be forgotten.

### Traps each hook was written around

- ⚠️ **`acknowledge.py` reacts via `issues/comments/<id>`**, so hand it a comment id only for
  an issue comment. A *review* comment's id belongs to the **pulls** collection and would
  react to an unrelated comment. Empty falls back to the issue or PR itself.
- ⚠️ **`delegate.py` defaults a missing `Role:` stamp and says so.** Wrong is recoverable,
  silent is not — a run that quietly does nothing is indistinguishable from a broken workflow.
  ⚠️ **"Says so" means on the issue, not only in the log.** `DEFAULTED` was emitted to
  `$GITHUB_OUTPUT` and declared as a job output with **nothing reading it** — a required channel
  with no consumer, the same shape that shipped dead for the #475/#476 handoff, for `decisions` on
  the PR path, and for `docsCandidates`. One comment names the route **and its remedy**: the two
  default paths are a missing `Role:` stamp and a PR whose story cannot be resolved, and each is a
  one-line fix, so a warning without it would be noise. Upserted rather than appended — a re-run
  resolving the same way twice is one fact, unlike the decisions log where each round is its own
  record.
  ⚠️ **`report-route.py` writes it, not `delegate.py`, because the announcement has to follow the
  interception** — see *When the script has to guess*. Both outcomes share the comment's marker, so
  a later interception **replaces** an earlier guess rather than stacking under it.
  ⚠️ **The same defect one level up: `defaulted` and `reason` were job outputs nobody read.** The
  fix for the router's dead channel reproduced it at the job boundary. They are step outputs now,
  consumed inside the router job; a job-level declaration only invites a reader to assume something
  gates on them.
- ⚠️ **The log hooks rewrite ONE comment each, never one per run.** An epic with ten tasks
  across three roles would otherwise bury itself in thirty comments. They are also derived
  entirely from GitHub state — no model writes any part of them, which is the only reason
  they can be trusted as a status board.
- ⚠️ **AN EPIC'S ONLY DETERMINISTIC ANCHOR IS ITS OWN `Sequencing` SECTION**, and until it was read
  an epic's stories were never parented at all. A story's Branch line names *itself*, so it can
  never point at its epic; the fallback was a prose `epic #N` reference that **no prompt requires**
  — a risk this hook's own docstring names, and then depended on. Measured on epic #1112: six
  issues created, zero parented, the step green and reporting success.
  ⚠️ The section is **not a new marker** — `Sequencing` is the Architect's stated deliverable and
  `dispatch-next.py` already reads it, so parentage now derives from something the model must
  produce for another reason. ⚠️ **Scoped to the section, never the whole body**: an epic cites
  prior art, superseded issues and out-of-scope work, and adopting every `#N` would irreversibly
  parent unrelated issues.
- ⚠️ **IT RECURSES EXACTLY ONE LEVEL, because an Architect decomposing an epic creates TWO
  generations in one run.** The hook only ever ran for the triggering issue, so when the trigger
  was an epic the story→task pass never happened — the tasks' Branch lines resolved perfectly and
  nothing ever asked them. One level only: a task has no children, and unbounded recursion over a
  parent-derived rule is how a cycle gets built out of a convention.
- ⚠️ **`file-sub-issues.py` cannot key on prose alone.** Its first version matched a branch
  line plus an `epic #N` reference, and adopted a meta-issue that quoted the convention as an
  example. Checking the author is a bot is what makes it sound — with the accepted cost that a
  hand-written sub-issue is never auto-parented.
- ⚠️ **`branch-navigation.py` runs on the AUTHORS path too, and that is not redundancy.**
  `delegate.py` rule 4 routes straight to the stamped role whenever a `Branch:` line is present, so
  an issue filed with both routing lines already written — **which is what a good agent-filed bug
  looks like** — never reaches the Architect, and so never reached the hook that creates its branch.
  `setupBranch` resolves the base branch before anything else, so the authoring job then 404s and
  dies in ~3s, before the model is called (#744, #777).
  ⚠️ The deeper fault was treating the `Branch:` **line** as proof of the **branch** — a
  model-written block standing in for state, which is the anti-pattern this file already names.
  Running the idempotent hook once more is the cheap fix; it only ever handles the absent case.
- ⚠️ **A role labels only what it opens.** The stamp hook marks the triggering issue or PR;
  `finish-pr.py` labels the PR that run created. Nothing labels someone else's work.
- ⚠️ **`Closes #<issue>` is both a prompt instruction and a hook.** The model writing it puts
  the link where a human reads it; the hook is the net, because a missing keyword loses the
  close with nothing to signal it. ⚠️ **Unless the author reported `remaining`** — then the hook
  withholds the keyword rather than adding it. A forgotten keyword and a deliberately omitted one
  were indistinguishable, and the deliberate one lost.
- ⚠️ [E8] **`open-story-pr.py` calls `gh pr create`, so its job needs `pull-requests: write`** — and
  until that was noticed it had `read`, so the call 403'd **every time since the hook existed**.
  It had never once succeeded: every story PR in the consuming repo was opened by hand, while this
  file described the hook as the mechanism. A story branch then sat unmerged with nobody looking
  and its work was lost.
  ⚠️ **It warned rather than failing, which is what made it survive.** A `::warning::` fails no
  step, so the job stayed green and the gap was invisible from outside — the same shape as the
  `defaulted` output nobody read. It now **fails the step**: every benign case returns earlier, so
  reaching the create call and not creating anything is always a real problem.
  ⚠️ The general lesson, since this is the third instance: **a hook that is the sole mechanism for
  something must fail loudly when it cannot do it.** Best-effort is right for bookkeeping that a
  human would notice missing; it is wrong for the only thing that opens a PR.
  ⚠️ **AND FAILING LOUDLY IS NOT THE SAME AS FAILING USEFULLY.** For as long as it failed, it
  failed with *"open it by hand"* and no cause (#27) — on a hook where every benign path has
  already returned, so reaching that line always means a PR genuinely should exist and something
  refused. Every diagnosis therefore started from zero. It uses `team.gh_raw()` now and prints
  what `gh` said, plus the two causes that account for most of them — the *Allow GitHub Actions
  to create and approve pull requests* checkbox, and a job holding `pull-requests: read`. Naming
  them is not a diagnosis; the reason is. It is what stops the reader re-deriving both each time.
- ⚠️ **A job that can be triggered on a PR needs `pull-requests: write`, not `issues: write`, to
  say anything at all.** Commenting on a PR goes through the `/issues/{n}/comments` endpoint — so
  the API reads as if `issues` covers it — but the permission GitHub checks is `pull-requests`.
  Without it the host action cannot create its tracking comment, and because that comment *is* how
  a tag-mode run reports, the run **aborts at setup before the model is called**: `Resource not
  accessible by integration`. ⚠️ Diagnose it by the step that failed, not by `num_turns` — there is
  no result payload at all, which is a different fingerprint from the dead run that reports success.
  ⚠️ The trap is that the job works perfectly on issues, so the gap stays invisible until the first
  PR trigger, however long that takes.
- ⚠️ **The full transcript already exists on every run — `show_full_output` is not what captures
  it.** `claude-code-action` calls `writeExecutionFile` unconditionally, leaving the complete
  turn-by-turn at `claude-execution-output.json` and exposing its path as the `execution_file`
  output. `show_full_output` only decides whether that content is *echoed to the console*. So a
  consumer wanting transcripts should **collect the file**, never turn on console output — on a
  public repo the console is the whole internet, and an Actions artifact is no better because
  artifacts follow repository read access.
  ⚠️ **A transcript is tool calls _and their results_.** If a run ever read a file or ran a command
  that surfaced a credential, it is in there. Treat it as secret material wherever it lands.
  ⚠️ Two runs have now been diagnosed only as far as their result payload — `num_turns`, cost,
  denials — because nothing collected the file before the runner was destroyed. That payload can
  say a run stopped early; it cannot say **why**.
- ⚠️ **A HOOK CANNOT INHERIT THE HOST ACTION'S GIT CREDENTIAL, AND ASSUMING IT COULD MADE EVERY
  LANDING IMPOSSIBLE.** `actions/checkout` persists its token as `http.<server>/.extraheader`;
  the action's `replaceCheckoutCredentials` **unsets exactly that entry** and substitutes its own
  short-lived token in the remote URL, so the agent cannot read the job's credential out of
  `.git/config` (`src/github/operations/git-config.ts`). Correct for the agent, fatal for a
  post-hook: after a long model step the inherited token has expired and a bare `git push origin`
  fails `Invalid username or token`. Measured on run 31918402971 — twelve minutes in, the capture
  branch was never created and the run's work died with the runner.
  - ⚠️ **`git-push.sh` is NOT the fix**, though its presence in the base allowlist suggests it is.
    Reading it settles the question: it is a security wrapper that rejects flags and non-`origin`
    remotes, ending in a bare `exec git push origin "$REF"`. It supplies no credential.
  - **`team.authenticate_git()` is the contract** — it points `origin` at an explicitly
    authenticated URL built from the hook step's own `GH_TOKEN`, and every hook doing network git
    calls it first. ⚠️ It sets the **remote**, not a per-command URL: `git fetch <url> <branch>`
    writes `FETCH_HEAD` and never updates `refs/remotes/origin/<branch>`, so a caller comparing
    against `origin/<branch>` would silently read a stale ref.
  - ⚠️ **`team.scrub()` is not optional wherever git output is reported.** The token is in the
    remote URL, git echoes that URL in its errors, and Actions masks secrets in the **log** only —
    a hook posting git's stderr into an issue comment is writing outside that protection.
  - ⚠️ **A failed fetch used to read as "the ref does not exist."** `work-completion.py` derives
    the as-is case from `fetch` returning non-zero, so an auth failure presented as a missing
    branch — the wrong diagnosis, on the path that then pushes.
- ⚠️ **Keep long-lived credentials out of any job a model step shares** unless the workflow
  puts them in *step* env. Step env is per-step, so a scripted step can hold a token the
  model step beside it cannot read. Secret masking covers logs only — not an API payload a
  model could write.

### The sandwich

⚠️ **Two scripted phases, one at each end of a run**: `delegate` routes in front, `custodial`
checks behind, and both consult a model only where a script cannot decide.

⚠️ [E19] **The back half exists because the front half cannot answer its questions.** "Does this story
have tasks?" read 0 for *every* story at branch-creation time while creation ran before
`file-sub-issues.py` — dissolved by moving the Architect's `branch-navigation.py` call after it. "Was this branch ever used?" is not knowable until work lands, or does
not. "Did the Architect deliver?" is only knowable once it has stopped. Each of these was attempted
at the front and produced fragile logic; observing them at the back is simply cheaper. **Reach for
the back half before adding a predicate to the front.**

⚠️ **`always()` on the custodial job is the #430 trap, handled.** It needs every role job, most of
which skip on any run, and a job needing a SKIPPED job reports cancelled without it. `security`
already runs this shape for the same reason.

⚠️ **It holds no model step, and that is what lets its merge-time half hold `contents: write`** —
the only destructive capability anywhere in this system. Nothing untrusted executes in a job with
no agent in it.

⚠️ **THE BACK HALF CREATES BRANCHES; NOTHING DELETES THEM.** An earlier version swept branches
nothing had used — the wrong end of the problem, since they should never have existed. Branch
creation now happens **only** in the custodial phase, which is the first moment `sub_issues()` tells
the truth. ⚠️ **THE "ONLY WHEN IT HAS TASKS" HALF IS GONE (#1133), AND THAT EXCEPTION WAS THE ROOT
OF THREE FAILURES.** A story with no tasks used to get no branch, `delegate.py` blanked its
`story_branch`, and its `Branch:` line named a ref that did not exist with a compare link beside it
that 404'd. ⚠️ Rule 1 (an explicit handle) never applied that blanking, so `@claude/<role>` on such
a story handed the host action a ref it could not resolve and the run died in **3.6s before the
model was called** — while a *label* trigger on the same issue worked. ⚠️ **And it saved no branch
anyway**: #746 produced two `failure/*` branches and no story branch, so create-nothing made the
debris unpredictable rather than absent.

⚠️ **The rule is now an UPSERT, and it is CONTINGENT ON AN AUTHOR**: exists, leave it; absent,
create it at the default branch's head — from the **authors job alone**, whatever the author and
whichever routing rule matched. The Architect and the Researcher no longer call the hook at all.
⚠️ **A branch exists because an author is about to work, not because an issue was shaped.** Shaping
and answering produce nothing to commit, so a branch cut at those moments sits empty unless and
until someone is dispatched to it — and the authors job is the only one that passes `base_branch`
to the host action, so it is the only place a missing ref can 404. That makes the rule checkable
from the workflow rather than argued from the hook's internals.
⚠️ **It follows that the branch appears late, and that is intended.** A story shaped today and
worked next week has no ref in between; its `Branch:` line is a name the first author run makes
real, and nothing resolves that name before then. It also covers the case where an author is added
to a story that previously had none — a Researcher ran, an author was added later — with no
detection needed, because the upsert happens whenever an author runs.
⚠️ Epics and spikes still get none, and a PR trigger no-ops because `ISSUE` is blanked for it — the
host action checks out the PR's head and ignores `base_branch` entirely.
⚠️ **It also removes a class of arithmetic bug structurally.** With the ref always present,
`base_branch` is always set, so a run STARTS at the story branch and `origin/<named>..HEAD` is
exactly that run's contribution. The stale-ref comparison that made a no-op run look like it had
commits to land (#1110/#1111) cannot arise.
⚠️ **The cost, accepted:** a story branch that exists even when a run produces nothing. One
predictable branch per story beats an unpredictable absence — and nothing deletes branches here,
so "avoid creating one" was never balanced by cleanup.
⚠️ **Authors still run no git.** The hook commits and pushes; that is what made landings
deterministic and it is not reopened by this.

⚠️ **`branch-navigation.py` is one hook at every site, and the front/back split is gone.** The
Architect's call sits **after** `file-sub-issues.py`, so "does this story have tasks" is answerable
at creation time and the custodial job no longer creates branches at all. The authors' pre-call is
the #744 net unchanged: a task whose story branch is missing gets it created before `setupBranch`
can 404. A story worked as-is gets no branch from navigation — its named ref is CREATED by its
own landing: `work-completion.py` handles the owns-line case identically to a task except at the
end, where the issue is **never closed** (its PR targets the default branch, so GitHub closes it
natively on merge) and `open-story-pr.py` opens the PR immediately — no tasks to wait for. The
author's git exception is gone; every issue-triggered run edits, reports, and stops.

⚠️ **The obsolete note below is kept deliberately** — the sweep it describes was real, shipped, and
removed one PR later. Whoever reaches for deletion again should find the reason it was the wrong
answer.

⚠️ **A deletion is announced on the issue, not just logged** — the same `custodian-log` comment
`apply-repairs.py` appends to, so everything the custodian has done to an issue reads as one
history. This is the fix-and-report rule applied to the one action that removes something: a job
log is not reporting, and a branch that vanishes with no record is indistinguishable from one that
was never created. ⚠️ Only a **deletion** writes; every no-op path stays silent, or the log becomes
noise nobody reads.

⚠️ [E11] **The branch delete is safe by construction, not by care.** Two conditions, both required:
0 commits ahead of the default branch — so there is no content to lose — **and** the issue closed,
so nothing is about to arrive. Either alone is wrong: 0-ahead by itself would delete a story branch
whose first task has not run yet.

⚠️ [E2] **A scripted hook fed by model-written input is still model-driven.** Derive a hook's
input from something the model must produce for another reason, or from state it cannot
avoid creating — never from a block it was merely asked to leave behind.

⚠️ **`gh api` prints its error body to STDOUT**, so a 404 is indistinguishable from data to
anything that only checks whether output arrived. The parent endpoint 404s for anything
unparented, which is most issues, and `compare` 404s for a deleted branch. `team.gh()`
returns `None` on a non-zero exit and `gh_json()` parses only what succeeded, so an error
body can no longer reach a caller. ⚠️ Do not add a hook that runs `gh` any other way — this
trap survived being documented and was written again anyway, twice.

⚠️ **`team.gh_raw()` IS THE ONE EXIT, AND IT IS FOR REPORTING, NEVER FOR READING.** Dropping the
reason is right for a caller that only needs to know whether something worked, and wrong for a
hook whose whole job is the thing that just failed — `open-story-pr.py` failed the run with no
cause for as long as it existed (#27). So `gh()` still returns `None` and nothing changes for its
callers; `gh_raw()` hands back the `CompletedProcess` and is reserved for the message. ⚠️ **Never
parse its stdout** — that is the trap above, re-opened. ⚠️ **And anything printed from it goes
through `scrub()` first**: the token rides in the remote URL, `gh` and git both echo that URL in
errors, and Actions masks the **log** only, so a hook one edit away from posting this to an issue
is writing outside that protection.
