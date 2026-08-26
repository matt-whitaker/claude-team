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
4. On wake, verify by **jobs, steps, and outcomes — never the tracking comment**:
   - Task closed, handoff posted → post progress on the story, advance to the next wave.
   - Task open with `remaining` → the author says it isn't done. Read why; re-trigger or
     surface to the maintainer. Do not close it yourself.
   - Run failed or the task closed without a handoff → diagnose from the run's steps before
     touching anything. A setup failure has no result payload; read the failing step.
5. Repeat until the sequencing is exhausted.

## 3. The endgame

After the last task closes, confirm the story's PR exists, targets the right branch, and its body
reflects what landed. A missing PR is a diagnosis (the team documents the usual causes), never a
silence. Post the final state on the story and hand the maintainer the PR link.

## Throughout

- State posted at every transition, on the story issue. A fresh session must be able to resume
  from GitHub alone.
- **Sample the pools per story**: `gh api rate_limit` costs one core call and reports `used` for
  each. Record the delta with the wave state you already post, so a wasteful driver is a number
  rather than a feeling — and so hitting a limit is caught before it stops a drive.
- Labels and progress comments on this story are pre-authorized; merging, closing issues, editing
  bodies, and anything on other stories is not.
- If the same task fails the same way twice, stop driving and report — a driver that keeps
  re-triggering is suppressing the signal.
