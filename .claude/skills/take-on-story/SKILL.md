---
name: take-on-story
description: Drive a claude-team story end to end as the session-side driver — sequence its tasks, watch the runs, land the story PR. Use when the maintainer hands over a whole story ("take on this story", "drive #N"), on a repo whose cascade is dark.
argument-hint: [story issue ref]
---

You are replacing the cascade, not the roles. Every task still runs in CI; you decide *when*,
watch *whether it worked*, and keep the story's state legible. The conduct rules are in
`rules/claude-session.md` §Driving a story — this skill is the procedure.

## 0. Refuse the wrong repo

Read the stub (`.github/workflows/claude.yml`): a bot named in `allowed_bots` means a live
cascade, and two drivers race for the same labels. Say so and stop. Drive dark repos only.

## 1. Orient

Fetch. Read the story issue fresh: its branch line, its sequencing section, its open tasks, any
handoff comments already posted. The team's own files define what these mean — read them from the
consuming repo, don't assume. Post one comment on the story: driving begins, which wave is next.

## 2. The wave loop

1. Reconcile: re-read the story and its tasks from GitHub. Never act on remembered state.
   ⚠️ **One batched query per transition, and prefer REST.** `gh issue view` / `gh pr view` /
   `gh run view --json` bill the **GraphQL** pool; `gh api repos/{o}/{r}/issues/{n}` and
   `.../actions/runs/{id}` bill **core** — two independent budgets, and concurrency drains GraphQL
   first. Driving three stories exhausted it twice in one hour while core sat near a quarter used
   (#93). Ask for every task and story in one aliased GraphQL query rather than one call each; it
   is also the only *consistent* read, since separate calls describe separate moments. Read
   immutable state — titles, the task list, the `### Sequencing` section — once at drive start,
   not every tick.
2. Label the next wave's task with the front-door label (your `gh` is the maintainer's account —
   a human-actor event; no App required).
3. Find the run it started (`gh run list`, newest, matched to the task) and park
   `gh run watch <id>` as a background task. Do other work or wait; the exit wakes you.
   ⚠️ On taking the story, also arm a **heartbeat** — a scheduled re-check on a long interval
   (20–30 min). A tick that finds everything in flight is a silent no-op; a tick that finds a
   dead watcher re-parks it; a tick after your own death is the resume. One heartbeat sweeps
   every story you are driving.
   ⚠️ **ITS COMMONEST CATCH IS NOT A DEAD WATCHER — IT IS A WAVE THE DRIVER FORGOT TO ADVANCE.**
   A watcher wakes you once, for one run. Anything that pulls you away between that wake and the
   next label — a question, a second story, a diagnosis — leaves the story finished-but-unadvanced,
   and nothing wakes you again: the repo is session-driven, so no cascade will do it for you. A
   living driver strands a story exactly as effectively as a dead one, and it looks identical from
   outside. Measured driving five workstreams at once: a task closed, an interrupt arrived mid-wake,
   and the next wave was never labelled until the maintainer noticed.
4. On wake, verify by **jobs, steps, and outcomes — never the tracking comment**:
   - Task closed, handoff posted → **harvest it** (below), post progress, advance to the next wave.
   - Task open with `remaining` → the author says it isn't done. Read why; re-trigger or
     surface to the maintainer. Do not close it yourself.
   - Run failed or the task closed without a handoff → diagnose from the run's steps before
     touching anything. A setup failure has no result payload; read the failing step.
5. Repeat until the sequencing is exhausted.

### Harvesting a handoff

⚠️ **READ THE HANDOFF'S CONTENTS, NOT ITS PRESENCE.** Four channels are forced out of every author;
two reach an automated reader on their own and two reach nobody unless you carry them. A story can
run green to completion with both accumulating on its issue and nothing consuming either. Measured
across twelve closed stories: seventeen `docsCandidates` and fourteen `supersedes`, none actioned.

Parse the JSON block in each handoff comment and carry it to the endgame:

| channel | what you do with it |
|---|---|
| `remaining` | already handled in step 4 — the task is not finished |
| `testingNotes` | nothing; the Tester reads it on its own trigger |
| `docsCandidates` | accumulate, and discharge at the endgame |
| `decisions` | a hook appends them to a running log on the story, so the record keeps itself. Its `supersedes` field does not: carry each one to the endgame and report what now reads the old way |

⚠️ **A candidate names a document, never an agent-instruction file** — the schema refuses those,
because the Writer is barred from them exactly as the authors are. What reaches you is a
specification or a reference that a late discovery left saying the wrong thing: small, concrete,
and worth applying. A fact belonging in agent instructions arrives under 🔔 Maintainer instead,
and that is the maintainer's to act on.

⚠️ **An empty array is an answer and needs nothing.** The author considered it and found nothing;
that is not a gap to chase.

⚠️ **Sweep before you rest, and after every interruption.** Whenever you are about to go idle — and
whenever anything pulls you off the loop — reconcile **every** story you hold, not just the one you
were last touching. One batched query answers it: for each story, is there a closed task whose
successor carries no label? That is a stranded wave, and it is the driver's to label now. Going
idle without that sweep is how a story stops silently.

## 3. The endgame

After the last task closes, confirm the story's PR exists, targets the right branch, and its body
reflects what landed. A missing PR is a diagnosis (the team documents the usual causes), never a
silence. Post the final state on the story and hand the maintainer the PR link.

Then discharge what you harvested:

- **`docsCandidates` → a follow-up PR, after the story's PR has landed.** One PR per story,
  applying the notes you accept to the files they name. ⚠️ **Never onto the story's own branch**:
  the last candidate arrives from the last task, by which point that PR is open or merged, and a
  documentation fix reviewed on its own is worth more than one appended to a diff about something
  else. ⚠️ **A candidate is a proposal.** Weigh each, apply what earns its place, and say which you
  dropped and why — rejecting all of them is a correct outcome.
- **`supersedes` → report, do not edit.** Each one names something that now reads the old way — an
  issue's acceptance criteria, a spec id, a sibling task. Editing an issue body is not pre-authorized;
  list them on the story with what each points at and let the maintainer act.
- **🔔 Maintainer and ❓Blocked sections → surface them.** A question whose only reader was the
  run's own transcript has no reader at all.

⚠️ **Where a finding pokes at the scope of the subject matter, ask rather than act.** The licence
here is to discharge what the authors already decided, not to widen the story.

## Throughout

- State posted at every transition, on the story issue. A fresh session must be able to resume
  from GitHub alone.
- **Sample the pools per story**: `gh api rate_limit` costs one core call and reports `used` for
  each. Record the delta with the wave state you already post, so a wasteful driver is a number
  rather than a feeling — and so hitting a limit is caught before it stops a drive.
- Labels and progress comments on this story are pre-authorized; merging, closing issues, editing
  bodies, and anything on other stories is not.
- ⚠️ **An interrupt does not pause the stories.** Answering a question, diagnosing another repo, or
  taking new work does not suspend anything you are driving — runs keep finishing and waves keep
  coming due. Sweep when you return.
- If the same task fails the same way twice, stop driving and report — a driver that keeps
  re-triggering is suppressing the signal.
