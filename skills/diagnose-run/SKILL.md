---
name: diagnose-run
description: Read a claude-team workflow run the way its record says runs must be read — by jobs, steps, and fingerprints, never the tracking comment. Use when a run failed, a task stalled, a cascade went quiet, or a result looks wrong in any repo running claude-team.
argument-hint: [run id or task ref]
---

The tracking comment looks identical in success and death, and `gh run list --limit 1` happily
hands you the wrong run. Resolve the run from the task (`gh run list` matched on the task ref),
then read **jobs → failing step → that step's log**.

⚠️ **Read runs over REST**: `gh api repos/{o}/{r}/actions/runs/{id}` and `.../runs?per_page=N` bill
the `core` pool, while `gh run view --json` bills **GraphQL** — the pool a driving session drains
first, and the one that stops a drive when it empties (#93).

## The fingerprints

Match before theorizing — each of these was measured, and each points at a different fix:

- **Dies in ~3s, no result payload, before the model** — a setup failure. The two commonest:
  the actor guard (*"Workflow initiated by non-human actor"* — a bot actor the stub's
  `allowed_bots` does not admit; on a rename, a stale slug) and a missing base branch (404 in
  `setupBranch` — the story's named ref does not exist yet).
- **Run reports success, task did nothing** — the dead-run shape. `num_turns` small, seconds of
  model time: check `trigger_phrase` extraction (a handle swallowed as a slash command) and the
  backgrounding stall (a tidy checklist, boxes unticked).
- **Model step failed at env validation in seconds** — the OAuth token is missing or lapsed.
  Everything scripted still ran; only the model half is dark.
- **Every step green, next task never started** — read the dispatch step's notice: dark cascade
  (declared off — the driver labels by hand) is a `::notice::`; admitted-bots-but-no-token is an
  `::error::` and means the App is not installed on the repository.
- **Task closed but no handoff on the story** — distinguish three states: entries, explicit
  `[]`, and **absent**. Absent means no author ran or it died before posting: re-trigger, do not
  close by hand.
- **`Resource not accessible by integration` at setup** — the job needs `pull-requests: write`
  for its tracking comment on a PR trigger; the permission checked is not `issues`.

## Conduct

- The full transcript exists on every run (`claude-execution-output.json` via the
  `execution_file` output) — collect it before the runner ages out; treat it as secret material.
- A finding against landed work is an ad-hoc commit on the story branch or a **new task** —
  a landed task never reopens.
- The same failure twice on the same task is a stop-and-report, not a third trigger — repeating
  the re-trigger suppresses the signal.
- Fix and report, never fix quietly: the diagnosis goes on the issue where the next reader
  finds it, not in the void of a job log.
