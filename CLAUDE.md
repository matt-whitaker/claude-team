# claude-team

A portable Claude + GitHub agent team: the role prompts, the scripted hooks around them, and the
workflow that runs them.

⚠️ **The gate is the test suite**: `python3 -m unittest discover -s tests` — stdlib only, no
dependencies, runs anywhere. The harness copies each hook into a scratch directory beside a
scripted `team` stub (Python resolves imports from the script's own directory before PYTHONPATH),
imports the pure text helpers from the *real* `team.py` so they cannot drift, and runs every git-touching case against real repositories — including
deliberately stale refs.

⚠️ **Releasing**: check out mainline, rename `CHANGELOG.md`'s `## Unreleased` heading to `## vN`
and open a fresh empty one above it, flip every pin (`TEAM_REF`, the in-workflow `@refs`,
`load-prompt`'s default, the stub template) from `mainline` to `vN` in one commit, run the suite
(`ReleasePins` asserts the agreement), tag that commit `vN`, push the tag, and **do not merge the
release commit** — mainline keeps its canary pins. Consumers pin `@vN`; a repo whose job is to
exercise the engine tracks `@mainline` instead — brewdocs.beer as the canary, `claude-team-example`
as the drill target, and this repo's own stub, which `SelfInstall` pins there permanently.
brewdocs.beer-kb also tracks `@mainline`, by the maintainer's call rather than by the rule.

⚠️ **THE SUITE CANNOT SEE WHICH COMMIT GOT TAGGED, so the release ends with a check on the tag
itself.** `ReleasePins` asserts the four pins agree with *each other* — on mainline they all read
`mainline`, so it is green on exactly the tree a mis-cut tag ships. Nothing else looks either. The
stub is the consumer's own pin, which makes it the sharpest single probe:

```bash
git show vN:templates/consumer-stub.yml | grep 'team.yml@'   # must print @vN, never @mainline
```

⚠️ **The plausible mis-cut is tagging the default branch's head.** The release commit is
deliberately not on any branch, so every tool that defaults to a branch — the GitHub Releases page
included — targets the wrong commit while looking exactly right. What ships is a `vN` whose jobs
fetch every hook and prompt from `mainline` at run time and a stub telling the consumer to pin
`@mainline`: pinning that pins nothing.

⚠️ **A release is not finished when the tag is pushed.** `ONBOARDING.md` §0 is the returning
consumer's path and `CHANGELOG.md` is what makes it answerable. A consumer has one question — *must
I act?* — so every version heading carries an explicit `**Action required:**` line and a test
asserts it. `no` is the commonest answer and the most valuable one.

⚠️ **The entry is written in the PR that causes it, not at release time**, which is why
`## Unreleased` stays permanently open. Reconstructing consumer impact from a merge log is the work
the file exists to remove, and it is done worst by whoever is trying to cut a tag.

⚠️ **A pin cannot express repo state.** Labels live in GitHub, not in the clone, so no ref bump
reaches them. §0 re-runs the label loop, the board placement and the Actions settings
unconditionally.

⚠️ **An overlay composes after the base and therefore WINS**, so a base change narrowing what a
role may do reaches nothing while an overlay still grants it. §0 says to grep for the old grant
whenever an entry reports a narrowed scope.

⚠️ **The consumer contract**: `team.yml` is a reusable workflow (`on: workflow_call`). A consumer
holds the frozen stub (`templates/consumer-stub.yml`) plus a `.claude-team/` directory — `prompts/`
overlays (`_shared.md` required) and an optional executable `setup.sh`. Inputs: `project_owner`,
`project_number`, `allowed_bots`, `node`, `browser`, `runtimes`. ⚠️ **Two pins move together**: the
consumer's `@ref` on the workflow, and `TEAM_REF` inside it (what the jobs fetch at run time) —
release tooling owns keeping them equal.

**Purpose.** A portable Claude/GitHub role team: the prompts each role runs on, the scripted hooks
around them, and the handoff contract between them. Consumed by pointing a workflow at these files;
extended by a per-role overlay in the consuming repo.
**Where.** `prompts/_shared.md` + `prompts/<role>.md`, `hooks/*.py`, `schemas/handoff.json`.
**Invariants.** `RULES.md` names the design rules this package holds itself to. A ⚠️ paragraph here
may cite one by opening with its id.
**[E1]** Routing is a script first: state decides wherever state can, and a model is consulted only
where it cannot, with the script's own answer as the floor when the consultation fails.

## Working in this repo

- Board: **9** (Claude Team). ⚠️ Not reachable from a cloud session; see below.
- Branch naming: `<issue#>-<kebab-summary>`, unless the session arrived pinned to one.

⚠️ **A session may arrive already pinned to a branch** it should stay on, for session coherence.
Prefer that branch over the naming convention, and say so rather than silently renaming.

⚠️ **THIS REPO RUNS THE TEAM WORKFLOW ON ITSELF.** The literal front-door handle — and any
`<handle>/<role>` form — in an issue or PR comment **starts a real run**, and backticks do not
protect it. Write around it: say "the front-door label". Applying those labels is the maintainer's
gesture alone.

⚠️ **A run here executes the hooks at `mainline`, not the ones in your checkout.** Editing `hooks/`
on a branch changes nothing about the run editing them. Merging changes the machinery for this
repo, `claude-team-example`, and every consumer tracking mainline at once.

⚠️ **This file is the specification.** There is no product spec; the Tester derives intent from
it, so editing it changes the contract.

⚠️ **A schema injected into a workflow step must contain no single quote** and must stay on one
line — `--json-schema` takes inline JSON wrapped in single quotes, and the argument list is parsed
line by line. The same applies to any comment: `claude_args: |` is a literal block scalar, so a
`#` line inside it reaches the CLI as an argument. Comments go above the block.

⚠️ **Label writes and board placement need a LOCAL session.** `ONBOARDING.md` §4's label loop and
board placement cannot be done from a cloud session — say so and hand over the command rather than
improvising.

## The issue hierarchy

| level | branch | its PR targets | closed by |
|---|---|---|---|
| **Epic** | none | — | its stories closing |
| **Spike** | none | — | the maintainer, once they have decided |
| **Story** | `<story#>-<summary>`, named by the Architect | the **default** branch | its PR merging |
| **Task** | none of its own — its work lands on the story's branch | — | `work-completion.py`, once its work has landed |

- An epic never has a branch and never has a PR. If something needs a PR, it is a story.
- A story owns one branch and one PR against the default branch, and it accumulates.
- A task is a slice of a story. It has **no PR**; its commits land on the story's branch.

⚠️ **An unprocessed issue is a STORY.** An epic has to say so — by an `epic` label or a title
beginning "Epic" — and the Architect leaves both markers behind. Deliberately NOT inferred from
having sub-issues: a story has those too, they are its tasks.

⚠️ **A maintainer's comment is the only override**, and it is judged by the model rather than
matched by the script. A regex for the word misfires on an ordinary sentence — "a story under the
Claude Team epic" — and a false positive decomposes a story into stories.

⚠️ **Epics are the maintainer's to create.** No role files one on its own initiative and none
promotes an issue into one. A role may *propose* an epic and stop. Ambiguity resolves to a story,
always.

⚠️ **A `spike` is a question, and it is the one unshaped issue the Architect must not take.** Its
answer is not known yet, so there is nothing to decompose — handed one, the Architect cuts
implementation tasks for a solution nobody has chosen, which reads like progress and is worse than
nothing because the tasks then get worked. `delegate.py` rule 3 routes it to the **Researcher**.
Like an epic it has no branch, no PR and ships no code; unlike an epic it is not a container, so it
has no children either.

⚠️ **A `bug` is a story in shape but not in handling.** One branch, one PR, usually one task — but
its body is the deliverable of an investigation that already happened, so the Architect **appends
and never rewrites**. A report's reproduction, its measurements and especially its "what I could
not determine" section are the only grounding the fixer has.

⚠️ **`team.kind()` returns `epic | spike | bug | story`, and `epic` wins** when an issue carries
more than one marker, so it resolves the same way every time.

⚠️ **Two kinds of label, and only one is the maintainer's.**

| kind | labels | who applies | what it means |
|---|---|---|---|
| **routing** | the front-door label, `@claude/<role>` | the maintainer; hooks stamp the trail | what should *happen* to this issue, and what has already run |
| **classification** | `epic`, `spike`, `bug`, `task`, `story` | anyone filing; the custodial phase fills gaps | what this issue *is* |

A classification label is durable and derivable, so it survives a run. ⚠️ **Every kind gets one,
`story` included** — `kind()` derives story from the absence of the other markers, but a board
cannot filter for "the ones with nothing".

⚠️ **`task` is derived from structure, not a marker.** A task's `Branch:` line names its **story's**
branch, so the number it starts with is not its own; a story's names itself. `kind()` uses exactly
the test the PR-base rule uses, so the two cannot disagree. ⚠️ It is checked **after** the marker
kinds: an explicit title prefix beats an inference.

⚠️ **The custodial phase labels the TASKS.** The trigger-time pass only ever reaches the trigger,
so a story got a label and the tasks the Architect had just created never did. The back half runs
after `file-sub-issues.py`, the first moment those children are discoverable. It only ever **adds**
— an issue already carrying a kind is left alone, because a maintainer who relabelled by hand meant
it. ⚠️ And it refuses to write when it cannot read the issue: `kind()` falls back to `story` on a
failed API call, so a rate-limited minute would otherwise relabel an epic.

⚠️ **The Branch line always names the STORY's branch** — on the story and on every one of its
tasks. It is what an author bases on and merges back into, never a branch for the task itself.

⚠️ **A story's Branch line carries a compare link**, appended by `branch-navigation.py` after the
closing backtick, so opening its PR is one click. One link serves the branch's whole life — GitHub
redirects a compare URL to the existing PR once one is open. ⚠️ The link sits **outside** the
backticks because `branch_line` is anchored and captures only what is between them; trailing text
must stay outside.

## Sequencing

⚠️ **Stories are independent; a story's tasks are ordered.** Two different defaults, each stated
where it can be seen:

- **Between stories** — independent unless the **epic's own body** says otherwise. A dependency
  written only in the dependent story is not enough.
- **Within a story** — the Architect's `### Sequencing` section is the contract: numbered lines,
  one wave per line, several refs on a line running in parallel. `dispatch-next.py` consults it to
  start the next wave; a task the section forgot is appended in derived `(phase, issue number)`
  order rather than stranded, and with no section at all tasks run one at a time in that derived
  order.

⚠️ **A section that parses to nothing is not the same as no section.** `sequencing_refs()` reads
refs only from lines that *start* with a number, so a section written as prose reads correctly to a
human, satisfies any check looking for the heading, and carries no instruction at all. Both callers
warn on it. The fallback to derived order is deliberate; doing it in silence is what cost the
diagnosis. ⚠️ [E14] A test parses every Sequencing example in the Architect prompt: a worked example
outranks the prose around it, and prose review does not catch one that parses to nothing.

⚠️ **The numbered form is containment, not documentation.** A task the section forgets is appended
*after* the listed waves, deliberately — so a task mis-parented onto the wrong story runs last. With
the section inert everything falls to derived order, that foreign task sorts by its role phase, and
a stray `writer` dispatches ahead of the story's own implementor.

⚠️ **An epic's section is prose and that is correct** — two forms, two parsers.
`file-sub-issues.py` takes any `#N` on any line of an epic's section, so the inline form is
legitimate there; the identical form on a *story* is the defect above. The custodial check is scoped
behind the epic/spike return, and a test pins both so nobody harmonises one example to the other.

⚠️ **The first wave needs its own ignition.** `dispatch-next.py` chains task N to task N+1 from the
authors job, so a story could be *continued* but never *begun*. It also runs **post-Architect**,
once a freshly-shaped story has its branch, and **inside `delegate`** for a story that arrives
already shaped. Three call sites, one hook: it finds the earliest incomplete wave.

⚠️ **A dark cascade must say why.** The token check lives in the **hook**, which separates the two
cases by volume — no secrets is the configured-off state and stays a `::notice::`; secrets present
with no token is a misconfiguration only a human can fix and is an `::error::`. The commonest cause
is an App that is authenticated but **not installed on the repository**, whose signature is a 404 on
`get-a-repository-installation-for-the-authenticated-app`.

⚠️ **"Depends on" means MERGED.** A story whose tasks are all closed but whose PR is open has
delivered nothing to any other branch — which is why the epic's work log carries a **landed** column
beside the task count.

⚠️ **Trigger order is derived, never stamped.** Tasks sort by `(phase, issue number)`: phase from
the `Role:` stamp — the writer, then the authors, then the tester — and number within a phase,
because the Architect creates them in the order it intends. A task is ready once everything before
it is closed. Both inputs are things the Architect must produce for other reasons; a third stamp
naming an order would be a third line it could skip.

## Where work goes

⚠️ **The governing rule: work goes on the branch of the thing the run was triggered on.** Not a
branch the model picks, not a new one. Two modes fall out of it — an **issue** trigger means a fresh
task branch and one PR at the story level; a **PR** trigger means commit to that PR's branch and
open nothing.

⚠️ **The host action implements this already.** `setupBranch` checks the PR's state, and for an
**open** PR it checks out `headRefName` and **ignores `base_branch` entirely** — that input is read
only on the create-a-branch path, reached for an issue trigger or a closed/merged PR.

⚠️ [E13] **Committing to the story branch is CORRECT when the story's PR is what is being
discussed.** The no-commit-to-the-story-branch rule belongs to task runs, which have their own
branch. Stating it absolutely, alongside "open your PR against the story branch", left a run
obeying both only by inventing a third branch and a second PR.

⚠️ **More PRs is not more granularity.** A reviewer follows a conversation by reading its commits
as small diffs, in order, in the place the discussion is happening. A second PR splits that thread.
The commits already are the granularity.

⚠️ **No hook opens a second one either.** `finish-pr.py` resolves the PR from the current branch, so
on a follow-up it finds the existing one and its stranded-commit recovery never fires. That recovery
is for a run that committed and left *no* PR at all.

⚠️ **Branch creation is scripted, not prompted.** The host action mints its own branch for an issue
trigger and injects *"You are already on the correct branch. Do not create a new branch"*, which
contradicts any prompt telling a model to cut one — and which instruction wins is the model's call.

- **The story branch** — upserted by `branch-navigation.py` from the **authors job alone**: exists,
  leave it; absent, create it at the default branch's head. The Architect names it and nothing else.
- **A task's branch** — the action's own `base_branch` input, set to the story's branch. Configure
  the action rather than fight it.
- **A task's commits** — `work-completion.py` lands them on the story branch. There is no task PR.

⚠️ **A branch exists because an author is about to work, not because an issue was shaped.** Shaping
and answering produce nothing to commit, and the authors job is the only one that passes
`base_branch`, so it is the only place a missing ref can 404. ⚠️ It follows that the branch appears
late, and that is intended: a story shaped today and worked next week has no ref in between.

⚠️ **The hook never touches a branch that exists.** Absent is the only case it handles: an existing
branch may carry an author's commits.

⚠️ [E11] **Nothing deletes a branch.** After landing a task branch is 0-ahead and harmless; adding a
delete would put back the one destructive capability this system removed on purpose.

⚠️ **With the ref always present, `origin/<named>..HEAD` is exactly that run's contribution.**
Without it a story worked as-is is cut from the default branch while its named ref may be days old,
so the count includes the default branch's own history and is non-zero however little the run did.
⚠️ A fresh branch hides this entirely, so any sandbox that builds one passes.

⚠️ [E7] **"Did the run produce anything" is read from `landed_ref`, which `work-completion.py`
writes, never from a commit count.** ⚠️ [E4] A test asserts that every env var any hook reads is set
somewhere in `team.yml` — a var read and never set can only ever be empty.

⚠️ [E10] **A failed landing must not name the runner's branch as safe** — that ref is never pushed
and dies with the container. ⚠️ [E9] The capture pushes anyway when ahead-ness cannot be
determined.

⚠️ **A rejected landing reconciles by merge**: `work-completion.py` pulls latest, commits the merge
commit, and pushes. A merge that **conflicts** is not resolved by script — the step fails with
`unlandable=true`, the commits stay on the run's branch, and resolution is an Implementor call.
Never a force-push, never silence.

⚠️ **The race between two tasks on one branch is real and CANNOT be closed.** `concurrency.group` is
keyed on the issue and cannot be keyed on the story — the group is evaluated before any job runs, so
only the event context is available and expressions have no regex. Anyone reaching for that fix
should stop here. What replaces the guarantee is triggering a story's tasks one at a time.

⚠️ **Nothing gates a task.** Verify runs on `pull_request`; with no task PR it first fires on the
story's PR, with every task's diff accumulated. A `push:` trigger restores it and was declined.

## How a story moves

1. **Architect** shapes the story, **names** its branch on a `Branch:` line, and creates its tasks —
   each stamped with the role that should pick it up.
2. Each **task** is triggered on its own. Its author commits on the branch the host action cut for
   it and opens nothing.
3. `work-completion.py` commits the run's changes, lands them on the story's branch and closes the
   task — unless the author reported work `remaining`, which leaves it open with the list on it.
4. The **story's** PR accumulates all of it. The maintainer reviews and merges the story as a whole.

⚠️ **The story's PR opens when the LAST task completes.** The all-tasks-closed gate lives in
`open-story-pr.py`, so every call site inherits it identically. ⚠️ An unreadable or empty task list
degrades to open-when-ahead with a warning — an early PR is a nuisance, a story that can never get
its PR is lost work.

⚠️ [E5] **No commits is not the same as unfinished.** Some tasks are **checks** and their correct
outcome is that nothing changed. Only an explicit `remaining: []` closes the task; an absent handoff
leaves it open with "the author never reported — re-trigger it".

⚠️ **A task is closed by the landing hook, not by a keyword.** There is no task PR, so there is
nothing for GitHub to act on. **The story's PR still needs its keyword** — it targets the default
branch, so GitHub closes the story on merge the ordinary way. An **as-is story** producing no commits
stays open for the same reason.

⚠️ **A task reaches Done from the landing hook and nowhere else.** `close-merged-work.py` sets Done
from a merged PR, and a task has none. ⚠️ That step is gated on `closed`, not on the hook
succeeding: a task reporting work `remaining` is deliberately left open, and marching it to Done
would erase the one signal saying it is unfinished.

⚠️ **A landed task is Done. It does not reopen.** A Tester finding, or a pipeline failure, against
work that has landed becomes either an **ad-hoc commit on the story branch** or a **new task**.
Trigger order is derived from `(phase, issue number)`, so reopening an early number puts that task
back *ahead* of ones that have already landed. Nothing is lost: every commit is on the one story
branch either way.

⚠️ **A task still open when its story merges is a signal, not a gap.** It was abandoned, or its PR
never landed. Closing a merged issue's open children hides exactly the case worth seeing.

⚠️ **`pull_request` events run the workflow from the PR's base branch**, so a workflow fix does not
reach an in-flight story until the default branch is merged into it.

## Routing

**A label on an issue is the front door.** Applying it starts a run, and `delegate.py` reads the
issue's state to pick the role. The same label named in a comment does the same. A `@claude/<role>`
handle in a comment names the role outright and skips the inspection — the way to override a bad
guess.

⚠️ **A comment can ASK for work, and the script cannot tell.** *"I believe this branch needs to be
updated from its base"* is a request, and settling a bare mention straight to the conversational role
answers it with a role structurally unable to act. Rule 1b **consults**: the delegate-phase custodian
reads the comment and answers `claude` for a question or a working role for a request, before the
role jobs gate on the result. `claude` stays the fallback, so a failed, skipped or `undecided`
interception lands where the rule used to send it outright.

⚠️ **`consult` is not `defaulted`.** `defaulted` means the state that should decide is **missing** —
a real gap, worth announcing, carrying a remedy. `consult` means the script decided as far as state
allows and the only open question is a judgement about a sentence. `report-route.py` stays **silent**
on a consultation that changed nothing.

⚠️ **This is not a role chaining off another**, which remains forbidden. The maintainer triggered the
run; the router is deciding which role serves that trigger.

⚠️ **An unknown handle lands there too.** `@claude/nonsense` matches no role, so rule 1b catches it
and the root role can say there is no such role.

⚠️ **A story with tasks is never an author's to work — triggering it means START IT.** Rule 4 emits
`dispatch` and no role, every role job skips on the empty `roles`, and the first wave starts. ⚠️ **A
story with NO tasks still falls through to its stamped author** — the as-is path — and that bound is
what keeps the two cases apart.

⚠️ **A bare front-door handle on a TASK routes to the Custodian, deterministically.** A task's runs
happen from its story, so a human landing on the task itself is there because something did not
happen — presumed stuck, diagnosed rather than re-run. Decidable from structure, so it is a script
rule: the Delegator is for judgement, not for facts.

⚠️ **The Delegator may answer in the PLURAL** — a `roles` array, in run order, for a request that
genuinely names two deliverables. Each member is filtered against the allowlist independently: an
invalid member is dropped rather than voiding the answer, and `undecided` is only ever alone.

⚠️ **A handle skips the role decision, not the context.** It still resolves the story — from the
PR's head branch on a PR, from the issue's **Branch** line on an issue. Resolve it inside the handle
branch; do **not** fall through to the state-based rules, which would re-judge the role.

⚠️ **`trigger_phrase` must be the role's exact handle.** It gates nothing when a prompt is supplied,
but the action extracts everything *after* it as "the user request" and yields that as the final
content block, which the CLI scans for a slash command. Set to a bare front-door label,
`@claude/<role> do X` extracts as `/<role> do X` and is swallowed as an unknown slash command — the
run reports success having never called the model.

### When the script has to guess

⚠️ **A `defaulted` route means "ask", not "run".** Rules 1–4 decide from state; where the deciding
state is missing they fall back rather than stall. That default is a **floor**: the router job puts
the question to the root role first and runs the fallback only if it cannot answer.

⚠️ **It is a STEP in the router job**, and each alternative is ruled out:

| shape | why not |
|---|---|
| a new workflow run | an event created with the workflow token starts no run, by design |
| a job the roles `needs:` | a job needing a **skipped** job reports cancelled |
| a job that `needs:` the router | too late; role jobs gate on the router's outputs and have started |

A job cannot gate on a step inside itself. It *can* gate on an output that step produced.

⚠️ **The step's answer is filtered by an allowlist, not trusted because it matched a schema.** A
malformed answer, a failed step, a skipped step and `undecided` all arrive as the script's default
with its notice intact. **A failed interception must never mean nothing runs**, so the step carries
`continue-on-error`.

⚠️ **"All arrive as the same thing" is correct for the ROUTE and wrong for the REPORT.** Collapsing
every failure in the *log* makes "the model declined" and "the model's answer never arrived" —
opposite problems — look identical. The fallback branch names which it was: no output at all,
`undecided`, no `role` field, an unknown role, or a role with no `why`.

⚠️ **The interception ships a transcript like every other model step.** A routing decision is the
cheapest thing to leave unrecorded and the most expensive to lose: it runs for a second, it decides
what the whole rest of the run does, and its output is consumed by a shell step that keeps nothing.

⚠️ **`undecided` has to be a real answer**, or the schema manufactures a guess. An enum of roles
alone leaves no way to say "the issue does not tell me", and answering suppresses the guess notice
that would have flagged it.

⚠️ [E9] **`kind` is resolved for every issue trigger, and a guard that starts work fails closed.**
Written negatively, an unresolved kind — which prints as `n/a`, and `'n/a' != 'epic'` is true —
dispatched. Written positively, only a kind recognised as workable proceeds. That also survives
`team.kind()` falling back to `story` on a failed API call.

⚠️ **The interception decides the ROLE and nothing else.** The story, its branch and the issue kind
stay on the script's outputs: they are read from state and are not in doubt.

⚠️ **Announcing a default belongs AFTER the decision, not inside `delegate.py`.** Announcing a guess
before anything had been asked produced a notice describing a decision that never took effect.
`report-route.py` runs after resolution and says whichever actually happened.

⚠️ **Deciding correctly does not repair the issue.** The missing stamp is still missing and the next
trigger takes the same detour, so the remedy is carried on **both** outcomes.

### The label trail

⚠️ **The role stamp is a record, not a route.** Roles stamp `@claude/<role>` as they start. Nothing
routes off them.

⚠️ **The front-door label is spent at close — the closing hook swaps it for `@claude/complete`.** On
an open issue it means *in flight*, and that meaning is load-bearing: `dispatch-next.py` skips any
open task carrying it, so a stale one blocks the cascade forever. Both of `work-completion.py`'s
close paths swap it, and **every** issue on `close-merged-work.py`'s merge path — including ones it
did not itself close, because a story's own issue is closed natively by GitHub and no hook touches
it.

- ⚠️ The swap fires no workflow run: hook label edits use `GITHUB_TOKEN`, whose events start no runs.
- ⚠️ `@claude/complete` must exist in the repo, like every other label the hooks apply.
- ⚠️ A stale front-door label on an open issue is a **hand-removal** — removing it re-arms the issue
  as dispatchable, which is why no sweep does it automatically.

⚠️ **Guard the loop.** Every stamp is another `labeled` event. Gate the trigger on the label name
being *exactly* the front-door label, and exclude bot actors. Both hold independently, and a third
comes free: a stamp applied with `GITHUB_TOKEN` starts no run.

⚠️ **A cascade must be admitted by every actor guard, not just this package's.** Dispatching by App
means every cascaded run is authored by a bot, and the host action carries its own human-actor check
that refuses **at setup**. A consuming repo must also name the App in `allowed_bots`, and name it
**explicitly** — a wildcard lets any external App invoke the action with a prompt it controls. ⚠️ It
is a setup failure, so there is no result payload and `num_turns` cannot diagnose it.

## Roles

| role | picked up from | writes |
|---|---|---|
| `@claude` | its name in a **comment**, with no role handle; **and** a route the script had to guess | an answer, a role name, and repairs to process state. No code, no branch, no PR |
| Architect | an epic or an unshaped story | the issue, a story's branch name, and its tasks |
| Researcher | a spike | findings and a recommendation, appended to the issue by a hook — it holds no shell |
| Implementor | a task stamped `Role: implementor` | code, outside the design system |
| Designer | a task stamped `Role: designer` | code, inside the design system |
| Tester | a task stamped `Role: tester`, one per story | tests |
| Writer | a task stamped `Role: writer`, one per dividing story, run **first** | the product specification, then human-facing documentation |
| Security | every merge, plus its handle on a PR | issues it files |

⚠️ **No role owns the agent instructions.** Every `CLAUDE.md`, every `AGENTS.md`, everything under
`.claude/` or `.claude-team/` — the role prompts included — is out of scope for all of them. Those
files are the instructions the roles run on, so a role editing them rewrites its own operating rules
inside a story PR being reviewed for something else. Ordinary documentation is checked by whether it
reads true; an instruction change is only checked by what it makes agents do next time. ⚠️ [E17] The
prompt is the only enforcement today; a deterministic guard collides with **this** repo, whose
product *is* those files. ⚠️ It is pinned in **both** places — the prompt and the workflow's job
header — because correcting one leaves the other saying the opposite. ⚠️ A prohibition with no
outlet turns a finding into silence, so a role reports a stale instruction in its 🔔 Maintainer
section with the file, what is wrong, and what it would change it to.

⚠️ [E3] **Input provenance is the dividing line, not a shell.** Every authoring role has one, the
Writer included: a specification says what a user can do and see, which means starting the app and
driving it. ⚠️ [E18] **Which commands they hold is the consumer's to name** — the `runtimes` input,
defaulting to `npm,npx,node`, expanded into `Bash(<name>:*)` grants. The value is **sanitised, not
interpolated raw**: it lands inside the quoted `--allowedTools` string, which the action parses line
by line. ⚠️ **Resolving to nothing fails the step**, because an author with no runtime cannot run any
gate and the silence is the whole defect. ⚠️ `Bash(*)` was never available as the fix: the action
re-injects `GH_TOKEN` and `CLAUDE_CODE_OAUTH_TOKEN` into the agent's environment whatever the step
declares. ⚠️ The narrow roles are untouched — the Researcher holds no shell by design, and the
Custodian and Security are allowlisted by **subcommand**, because a family grant cannot express
"read but do not write".

### The Researcher

⚠️ **It answers; it does not shape.** It appends findings to the spike and stops — no story, no
branch, no author. The maintainer decides, and only then is there something to shape. ⚠️ **It
appends and never rewrites the question**: the maintainer's framing carries which options they
already weighed and which constraint they called non-negotiable.

⚠️ **It is the only role that reads the open web, and the only one whose input the maintainer did
not write — which is why it holds no shell.** No `Bash` of any kind, no `Write`. It reads
(`Read`/`Glob`/`Grep`), it fetches, and it returns JSON. ⚠️ Taking the secret away instead is not available: the action re-injects
it whatever the step declares. Narrowing rather than removing would not hold either — `Write` plus
any runner is agent-authored code, so a probe spec *is* arbitrary execution.

⚠️ **A credential can reach the agent through a FILE.** `actions/checkout` defaults to
`persist-credentials: true`, writing the token into `.git/config` as an `http.<host>.extraheader`,
so a role holding nothing but `Read` can recover it. This role's checkout sets
`persist-credentials: false`. ⚠️ Only this one's: an authoring job pushes.

⚠️ **`WebFetch` is itself an egress channel**, so a narrower `Bash` grant was never the fix. Only the
absence of a way to *read* the environment closes it.

⚠️ **It carries no `id-token` and passes its own `github_token`, and those two are one change.**
`setupGitHubToken()` mints an OIDC token and exchanges it for an App token, so with no OIDC and no
supplied token the action cannot authenticate at all. ⚠️ And it is what makes a `permissions:` block
mean anything to the agent: that block scopes `secrets.GITHUB_TOKEN`, not the App token the exchange
mints. **Every other role still takes the App-token path**, so their blocks bound their hooks and not
their models.

⚠️ **The residual, written down rather than claimed away:** the action's base allowlist unions in
`Bash(git add|commit|rm:*)` and `git-push.sh`, and a role cannot remove them. Two things neuter them,
in order: there is no `Write`, so the agent cannot author a file worth committing; and
`contents: read` bounds the token — **but only because `github_token` is passed**.

⚠️ **A spike that reports only what it settled is not finished.** What it could *not* determine is
the section under the most pressure to skip and the most valuable to keep.

### The custodian's repair remit

The root role is the only one that may put **process state** right — the breakage no role owns.

⚠️ [E3] **It names repairs; a hook applies them.** The model returns JSON, `apply-repairs.py` acts on
it, and the hook's repertoire is a fixed enum — `board-item`, `sub-issue-link`,
`classification-label`. That makes "never touches content" a fact about what it can **reach**. ⚠️
`gh api` is deliberately absent: it reaches every endpoint the token has. Relationships survive that
narrowing because `gh issue view` exposes `parent`, `subIssues` and `subIssuesSummary` — checked
before narrowing, because too narrow starves a role silently.

⚠️ **It holds direct git and `contents: write`, by the maintainer's decision.** What remains
structural: it holds no `Write`/`Edit`, so it can move refs but has nothing of its own to commit;
`github_token` is passed, so the job's `permissions:` block is what its token actually gets; and
every run's transcript is captured.

⚠️ [E12] **Fix AND report, never fix quietly.** Every repair appends to one log comment on its target
carrying *what was wrong* and *why*. ⚠️ **A repeat escalates instead of repairing**: reaching for the
same `kind` on the same target twice means the cause was never fixed, so the hook withholds the
repair, files an issue, and leaves the instance broken on purpose. The check reads the log comment —
state on the issue, not a memory of the last run.

⚠️ [E4] **`unrepairable` is the other half and carries the weight.** Anything outside the enum,
anything needing content changed, and anything whose real fix is upstream in a rule goes there with
what would fix it. **It reports onto the trigger**, because a finding carries no target of its own —
the schema gives it `what` and `wouldFix`. ⚠️ Commenting on a PR needs `pull-requests: write`, not
`issues: write`. ⚠️ [E6] Same comment marker as the repairs, and it **appends**: a finding that
recurs is the signal its cause is still there, and an upsert would erase it.

⚠️ **The answer still goes in the tracking comment.** With `--json-schema` the final message is JSON,
so `track_progress: true` is the only place a human reads a reply.

⚠️ **Three jobs, two prompts.** `claude.md` is the conversation — someone asked it something.
`route.md` is the interception — nobody asked it anything, and its whole output is a role name plus
the reason. A conversational prompt handed a routing decision answers in prose; a routing prompt
handed a question answers with an enum. ⚠️ `route.md` is loaded by a STEP, so it runs in agent mode,
and losing the tracking comment is the better outcome there — the durable record is
`report-route.py`'s comment. `structured_output` is set after the run in either mode, so the schema
still binds.

### Implementor, Designer, Tester, Writer

⚠️ **Implementor and Designer split on the package a change touches, not on judgement**, so the
boundary can be checked rather than negotiated. ⚠️ **But the Designer repairs the consumers its own
change breaks** — a primitive is an API, and the same role is told to hand over a green gate. The
licence is bounded by a checkable line: **repair what your change broke, never what was already
broken**, and keep it mechanical. A consumer needing a *different value* is a behavioural decision,
still the Implementor's. ⚠️ A task spanning both is two tasks only when the consumer half is
behavioural.

⚠️ **A test derived from the implementation is worthless, and looks exactly like coverage.** It
asserts what the code does, so it passes by construction. The Tester derives from *expected*
behaviour — the **product specification** first, then the story's outcome, the `testingNotes`, the
acceptance criteria — and may read a component for one thing only: how to **address** an element.
⚠️ The specification is the only one of those that outlives its story; the Tester cites behaviour ids
in its plan, which is what makes coverage a question a reviewer can ask.

⚠️ **A failing test is a finding, not a chore.** It is filed on the authoring task, carried in the
Tester's report, and left failing. A green suite that got there by deletion is worse than a red one.

⚠️ **The Writer owns the product specification, and that is why it runs FIRST.** A specification
cannot say what the code *should* do if it was written by reading the code that already exists.
Ordering the Writer ahead of the authors makes "from intent, not from the diff" true by construction.

⚠️ [E13] **Its task is cut on every story THAT DIVIDES, and inside that scope it is unconditional.**
The scope is what keeps it from contradicting *"a story one author can finish should not be split"* —
two absolutes with no precedence stated leave a run to disobey one silently. ⚠️ Softening the rule
instead reverts to the failure that produced it. The discriminator is stated rather than felt: *does a specification need writing before the code?* Ambiguity resolves to
**divide** — an unnecessary Writer run is one cheap run reporting nothing to specify.

⚠️ **Running first strands `docsCandidates`.** The authors emit them after the Writer has finished,
so nothing consumes them in the same story. They stay on the story's issue and the maintainer
re-triggers the Writer on the same task once the authors land. The Writer's prompt tells it to say
whether it expects to be needed again.

⚠️ **Per story, not per epic.** An epic-wide documentation pass only avoids conflicts if stories land
in parallel; where they merge one at a time, deferring moves the explanation further from the change
it explains.

## The handoff between authors

An author's step carries `--json-schema`, so its final message is a contract: `remaining` for
whether the task is finished at all, `decisions` for the record, `testingNotes` for the Tester,
`docsCandidates` for the Writer. `post-handoff.py` posts it to the **story's issue** as one comment
per task, where the Tester reads it on its own trigger. The Writer reads it only on a **re-trigger**.

- ⚠️ [E5] **Three states, not two:** entries, an explicit `[]`, and no handoff comment at all.
- ⚠️ **The story's issue, not its PR.** The PR does not exist until the last task completes.
- ⚠️ **A PR follow-up must reach the story too.** The workflow blanks `ISSUE` on a PR trigger, so
  the hook needs `PR` as the other half; without it `decisions` has no path on the only trigger it
  exists for.
- ⚠️ **`remaining` is the only way an author can say it did not finish**, and leaving the closing
  keyword out of the PR body was never one — `finish-pr.py` asked whether the keyword was present,
  never why it was absent. A non-empty `remaining` now **strips** the keyword, the PR carries a
  warning block, and the task gets a comment listing what is left.
- ⚠️ **The schema beats the prose, deliberately.** A body is something a model can write anything
  into, including a closing keyword contradicting its own report. The forced channel wins over the
  skippable one; that is the whole reason there is a schema.
- ⚠️ **The withheld keyword becomes a bare `#N` reference, not nothing** — discoverable from the
  task while leaving `closingIssuesReferences` empty. ⚠️ `close-merged-work.py`'s fallback is a regex
  over the body, so the warning block's wording must never read as a closing keyword. Asserted.
- ⚠️ [E6] **`remaining` is upserted on the task; `decisions` is appended to the story.** What is left
  is a snapshot a later run supersedes; a decision is a record a later run must not erase. A PR draws
  several rounds of review, and round two replacing round one destroys the fact the comment exists to
  keep.
- ⚠️ **`decisions` is the antidote to a review that dies in its own thread.** A maintainer changes
  course on a PR; the issue still describes what they rejected, and nothing rewrites it. The next
  agent reads the old plan and rebuilds the rejected thing. **A PR comment is not a durable
  artifact.**
- ⚠️ **Reporting a decision does not discharge it.** `supersedes` names the specification, criteria
  or sibling task that now read the old way, precisely, so a human can go and fix them.
- ⚠️ **Deterministic at both ends:** the schema forces the author to produce it, the hook forces
  delivery. Asking a model to leave a machine-readable block for a later role is the version that
  fails.
- A candidate is a proposal, never an order. Rejecting all of them is a correct outcome.
- ⚠️ [E18] `docsCandidates[].file` is a **free string**, never an enum of a repo's paths.

⚠️ [E4] **The transport is the half that breaks, not the schema.** Appending it to the consuming
roles' prompts from the same job only works if those roles run in that job. They do not. A comment
outlives its run; a step output does not.

## Prompt composition

A role's prompt is `prompts/_shared.md` then `prompts/<role>.md` from this package, followed by the
consumer's overlay in the same order. The base says how the role behaves and how the hierarchy
works; the overlay says what the repo's gate is, where its code lives, and any house rules.

⚠️ **Shared first, and that ordering is load-bearing.** `_shared.md` opens by overriding the host
action's own prompt, which for comment events states repeatedly that the model's instructions are the
triggering comment. Ours arrives after all of that, so the override has to be the first thing in it.

⚠️ [E18] **Keep the split honest.** A rule true in any repo belongs in the base; a rule naming a
command, a path or a package belongs in the overlay.

⚠️ [E15] **A run ends with a deliverable or a named obstacle.** Three failure shapes, and the
discriminator differs for each:

- **Stopping early** — a tidy checklist with the boxes unticked. ⚠️ [E16] The cause is
  **backgrounding**, not giving up: the model launches a background subagent, calls a
  schedule-a-wake-up tool, and signs off believing it scheduled a resumption. The rule names the
  behaviour rather than the feeling, and preserves synchronous delegation — a subagent invoked
  in-turn returns its result and works correctly. Forbidding delegation outright removes a useful
  capability to correct a default.
- **Stopping late** — grinding on one obstacle, producing nothing *and* explaining nothing. The
  discriminator is **non-convergence**: attacking the same obstacle with variations rather than steps
  forward is the signal to bank and report.
- **Gathering without producing** — every turn succeeds, every turn yields something new, the
  deliverable is still empty. Neither other discriminator fires. ⚠️ The check has to be **what is in
  the file I was asked to produce**, not "am I learning things".

⚠️ **A denylist is not available as the fix.** The backgrounding tools were in **neither** the role's
`--allowedTools` **nor** the action's base set, and executed anyway. An allowlist that does not bind
cannot be tightened into a denylist that does.

⚠️ **The host action's scaffolding contributes.** Tag mode asks the model to keep a todo list in its
tracking comment, which is a real, satisfying, visible action.

⚠️ **Stopping is not permission to invent** — that is the failure the stop exists to avoid, and it is
worse than either, because nothing about it looks wrong. ⚠️ **No issue body can require a role to
spend the whole budget**: an unmeetable acceptance criterion is a finding.

⚠️ [E14] **An issue's worked example outranks the prose around it, and a standing rule outranks the
issue.** An issue says *what* to deliver and ages in place; a rule about *how to work* is newer and
wins — and the role flags the stale example so it stops costing runs.

⚠️ **"Confirm scope" is the tell.** A plan step whose natural completion is asking a human has
planned its own failure — nobody is reading while a run executes. Ambiguity is not a stop condition:
choose a defensible reading, ship, and raise the question in the 🔔 Maintainer section.

⚠️ [E17] **The prompt is the second line of defence.** The custodial phase fails the run when the
deliverable is missing; the check is how anyone finds out, the prompt is what stops it.

## Hooks

Deterministic steps that run around each model step, so backlog bookkeeping cannot be forgotten by a
model that ran out of turns or simply skipped it. ⚠️ [E17] These were prompt instructions until a
model skipped them. A scripted step costs no turns and cannot be forgotten.

| hook | when | does |
|---|---|---|
| `acknowledge.py` | the router job, first | reacts 👀 so the trigger is visibly received |
| `delegate.py` | the router job | picks the role from issue state |
| `report-route.py` | the router job, last | says on the issue that this run did not route from state alone — whether the script guessed or the root role was asked |
| `labels-and-status.py` | around every run | one hook, three modes — `stamp`: `@claude/<role>` on the trigger; `kind`: the classification label (`INCLUDE_SUB_ISSUES` reaches the tasks); `status`: board place + Status |
| `branch-navigation.py` | pre, authors | upserts the story's branch and appends the compare link on creation |
| `file-sub-issues.py` | post, Architect | parents stories to their epic, tasks to their story |
| `work-completion.py` | post, authors | commits the run's changes (message from the handoff's `commitMessage`), lands them on the story's branch — reconciling a rejected push by merge — and closes the task; a **conflicted** merge fails the step with `unlandable=true` |
| `capture-failure.py` | post, authors — only on a failed model step or a conflicted landing | pushes to `failure/<task#>-<run#>-<attempt>` and appends a recovery report; never fails, never masks the real error |
| `dispatch-next.py` | post, authors when the landing **closed** the task; post, Architect; in `delegate` when an already-shaped story is triggered | reads the story's `### Sequencing` section and labels every open, unlabelled task in the earliest incomplete wave |
| `finish-pr.py` | post, authors | labels the PR and reconciles the closing keyword with `remaining`. Returns immediately for a task. Also the net under **stranded commits**: pushes the branch, opens a PR, and **fails the run** if either cannot happen — pushing first is what makes the recovery real, since `gh pr create --head` needs the branch on the remote |
| `apply-repairs.py` | post, the root role | applies the repairs it named, records each, reports what it would not fix onto the trigger, and files an issue rather than repairing the same thing twice |
| `post-findings.py` | post, Researcher | renders its schema-forced findings onto the spike — the role has no shell, so this is the only way they reach anyone |
| `post-handoff.py` | post, authors | posts the JSON handoff to the story's issue, and appends its `decisions` to one running log there |
| `log-to-story.py` | post, Architect + authors + on merge | rewrites one comment on the story listing its tasks in trigger order |
| `log-to-epic.py` | post, authors | rewrites one rolling work-log comment on the epic |
| `open-story-pr.py` | after a landing, on merge, and when a task is closed by hand | opens the story's PR once every task is closed. The `issues: closed` path passes `ISSUE` instead of `BASE` and resolves the story from the closed task's own Branch line |
| `close-merged-work.py` | on merge | closes the PR's issues and files them on the board |
| `custodial-sweep.py` | post, every role (`deliverable`) and on merge (`branches`) | checks what a run left behind: an Architect with no `Branch:` line fails the run |

### Traps

- ⚠️ **`acknowledge.py` reacts via `issues/comments/<id>`**, so hand it a comment id only for an
  *issue* comment. A **review** comment's id belongs to the `pulls` collection and would react to an
  unrelated comment. Empty falls back to the issue or PR itself.
- ⚠️ [E4] **A default route is announced on the issue, not only in the log**, and the notice carries
  its **remedy** — the two default paths are a missing `Role:` stamp and a PR whose story cannot be
  resolved, each a one-line fix. Upserted rather than appended: a re-run resolving the same way twice
  is one fact.
- ⚠️ **The log hooks rewrite ONE comment each, never one per run**, and are derived entirely from
  GitHub state — no model writes any part of them, which is the only reason they can be trusted as a
  status board.
- ⚠️ **An epic's only deterministic anchor is its own `Sequencing` section.** A story's Branch line
  names *itself*, so it can never point at its epic. ⚠️ [E2] The section is not a new marker — it is
  the Architect's stated deliverable and `dispatch-next.py` already reads it. ⚠️ **Scoped to the
  section, never the whole body**: an epic cites prior art and out-of-scope work, and adopting every
  `#N` would irreversibly parent unrelated issues.
- ⚠️ **`file-sub-issues.py` recurses exactly one level**, because an Architect decomposing an epic
  creates two generations in one run. One level only: a task has no children, and unbounded recursion
  over a parent-derived rule builds a cycle out of a convention.
- ⚠️ **It cannot key on prose alone**, or it adopts a meta-issue that quotes the convention as an
  example. Checking the author is a bot is what makes it sound, with the accepted cost that a
  hand-written sub-issue is never auto-parented.
- ⚠️ **`branch-navigation.py` runs on the authors path, and that is not redundancy.** `delegate.py`
  rule 4 routes straight to the stamped role whenever a `Branch:` line is present, so an issue filed
  with both routing lines already written never reaches the Architect. `setupBranch` resolves the
  base branch before anything else, so the authoring job then 404s and dies before the model is
  called. ⚠️ [E2] The deeper fault was treating the `Branch:` **line** as proof of the **branch** — a
  model-written block standing in for state.
- ⚠️ **A role labels only what it opens.** The stamp hook marks the triggering issue or PR;
  `finish-pr.py` labels the PR that run created. Nothing labels someone else's work.
- ⚠️ [E8] **`open-story-pr.py` calls `gh pr create`, so its job needs `pull-requests: write`.** It
  had `read`, so the call 403'd every time and every story PR was opened by hand while this file
  described the hook as the mechanism. ⚠️ It **fails the step** rather than warning: every benign
  case returns earlier, so reaching the create call and not creating anything is always a real
  problem. ⚠️ It prints what `gh` said, plus the two causes that account for most of them: the
  *Allow GitHub Actions to create and approve pull requests* checkbox, and a job holding
  `pull-requests: read`.
- ⚠️ **A job triggerable on a PR needs `pull-requests: write`, not `issues: write`, to say anything
  at all.** Commenting on a PR goes through `/issues/{n}/comments`, but the permission GitHub checks
  is `pull-requests`. Without it the host action cannot create its tracking comment, and because that
  comment *is* how a tag-mode run reports, the run **aborts at setup before the model is called**.
  ⚠️ Diagnose by the failing step, not `num_turns` — there is no result payload at all. ⚠️ The trap is
  that the job works perfectly on issues, so the gap stays invisible until the first PR trigger.
- ⚠️ **The full transcript already exists on every run — `show_full_output` is not what captures
  it.** `claude-code-action` calls `writeExecutionFile` unconditionally, leaving the turn-by-turn at
  `claude-execution-output.json` and exposing its path as the `execution_file` output.
  `show_full_output` only decides whether that content is echoed to the console. **Collect the file**,
  never turn on console output — on a public repo the console is the whole internet, and an Actions
  artifact is no better because artifacts follow repository read access. ⚠️ **A transcript is tool
  calls _and their results_.** Treat it as secret material wherever it lands.
- ⚠️ **A hook cannot inherit the host action's git credential.** `actions/checkout` persists its
  token as `http.<server>/.extraheader`; the action's `replaceCheckoutCredentials` **unsets exactly
  that entry** and substitutes its own short-lived token in the remote URL. Correct for the agent,
  fatal for a post-hook: after a long model step the inherited token has expired and a bare
  `git push origin` fails `Invalid username or token`.
  - ⚠️ **`git-push.sh` is NOT the fix**, though its presence in the base allowlist suggests it is. It
    is a security wrapper that rejects flags and non-`origin` remotes, ending in a bare
    `exec git push origin "$REF"`. It supplies no credential.
  - **`team.authenticate_git()` is the contract** — it points `origin` at an explicitly authenticated
    URL built from the hook step's own `GH_TOKEN`. ⚠️ It sets the **remote**, not a per-command URL:
    `git fetch <url> <branch>` writes `FETCH_HEAD` and never updates `refs/remotes/origin/<branch>`,
    so a caller comparing against `origin/<branch>` would silently read a stale ref.
  - ⚠️ **`team.scrub()` is not optional wherever git output is reported.** The token is in the remote
    URL, git echoes that URL in its errors, and Actions masks secrets in the **log** only — a hook
    posting git's stderr into an issue comment is writing outside that protection.
  - ⚠️ **A failed fetch reads as "the ref does not exist."** `work-completion.py` derives the as-is
    case from `fetch` returning non-zero, so an auth failure presents as a missing branch — the wrong
    diagnosis, on the path that then pushes.
- ⚠️ **Keep long-lived credentials out of any job a model step shares** unless the workflow puts them
  in *step* env. Step env is per-step, so a scripted step can hold a token the model step beside it
  cannot read.
- ⚠️ [E8] **`gh api` prints its error body to STDOUT**, so a 404 is indistinguishable from data to
  anything that only checks whether output arrived. The parent endpoint 404s for anything unparented,
  and `compare` 404s for a deleted branch. `team.gh()` returns `None` on a non-zero exit and
  `gh_json()` parses only what succeeded. **Do not add a hook that runs `gh` any other way.**
- ⚠️ **`team.gh_raw()` is the one exit, and it is for REPORTING, never for READING.** It hands back
  the `CompletedProcess` and is reserved for the message. ⚠️ **Never parse its stdout.** ⚠️ Anything
  printed from it goes through `scrub()` first.

## The sandwich

⚠️ **Two scripted phases, one at each end of a run**: `delegate` routes in front, `custodial` checks
behind, and both consult a model only where a script cannot decide.

⚠️ [E19] **The back half exists because the front half cannot answer its questions.** *"Was this
branch ever used?"* is not knowable until work lands, or does not; *"did the Architect deliver?"* only
once it has stopped.

⚠️ **`always()` on the custodial job is required**: it needs every role job, most of which skip on
any run, and a job needing a SKIPPED job reports cancelled without it. `security` runs this shape for
the same reason.

⚠️ **It holds no model step, and that is what lets its merge-time half hold `contents: write`** — the
only destructive capability anywhere in this system. Nothing untrusted executes in a job with no
agent in it.

⚠️ [E11] **The branch delete requires both conditions**: 0 commits ahead of the default branch,
**and** the issue closed. ⚠️ [E12] A deletion is announced on the issue in the same `custodian-log`
comment `apply-repairs.py` appends to; every no-op path stays silent, or the log becomes noise.

⚠️ [E2] Every hook here derives its input from something a role must produce for another reason,
or from state it cannot avoid creating.
