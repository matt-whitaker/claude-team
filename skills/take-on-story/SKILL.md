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
- Labels and progress comments on this story are pre-authorized; merging, closing issues, editing
  bodies, and anything on other stories is not.
- If the same task fails the same way twice, stop driving and report — a driver that keeps
  re-triggering is suppressing the signal.
