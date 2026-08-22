# CLAUDE_CLOUD.md

**template-revision: 1** · **SETUP revision: 2**

⚠️ **Read this only if you are a Claude Code *cloud* session.** A local session already has all
of it from the maintainer's memory and `~/.claude/`, and should stop here rather than spend
context on it.

You are a cloud session if any of these are set:

```bash
env | grep -E 'CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE|CLAUDE_CODE_CONTAINER_ID|CLAUDE_CODE_REMOTE_SESSION_ID'
```

This file exists because **nothing under `~/.claude/` reaches you** — no auto memory, no user
`CLAUDE.md`, no personal skills. It is the durable substitute, and it is committed, so it is the
only thing here that survives the container.

## This environment

- Repos live under `/home/user/`, not `~/Repositories/Claude/`.
- **There is no `gh` CLI.** GitHub is reached through MCP tools.
- The container is ephemeral. **Anything not committed and pushed is lost** — including
  anything you learn.
- Only the repos attached to the session are reachable. Another repo has to be attached before
  you can read it, even to answer a question about it.

## How work ships here

- Default branch: `mainline` — **not** `main`.
- Verification gate: `python3 -m unittest discover -s tests`. Stdlib only, no dependencies,
  runs anywhere. ⚠️ It is the gate — a change that has not run it is not finished.
- Board: **9** (Claude Team). ⚠️ You cannot reach it; see *Lessons*.
- Branch naming: `<issue#>-<kebab-summary>`, unless the session arrived pinned to one.

⚠️ A cloud session may arrive **already pinned to a branch** it should stay on, for session
coherence — the platform tracks changes against it. Prefer that branch over the naming
convention, and say so rather than silently renaming.

## Repo hazards a cloud session will hit

⚠️ **This repo runs the team workflow ON ITSELF.** The literal front-door handle — and any
`<handle>/<role>` form — in an issue or PR comment **starts a real run**, and backticks do not
protect it. Write around it: say "the front-door label". Applying those labels is the
maintainer's gesture alone.

⚠️ **A run here executes the hooks at `mainline`, not the ones in your checkout.** Editing
`hooks/` on a branch changes nothing about the run editing them. Merging changes the machinery
for this repo, `claude-team-example`, and every consumer tracking mainline at once.

⚠️ **`CLAUDE.md` is the specification here.** There is no product spec; the Tester derives intent
from `CLAUDE.md`, so editing it is a change to the contract, not to prose. Its ⚠️ paragraphs each
carry the failure that produced them — never delete a superseded one, mark it tried-and-wrong.

⚠️ **`gh api` prints its error body to STDOUT**, so a 404 is indistinguishable from data to
anything that only checks whether output arrived. Use `team.gh()` / `team.gh_json()`, which
return `None` on non-zero exit. This trap survived being documented and was written again twice.

⚠️ **A schema injected into a workflow step must contain no single quote** and must stay on one
line — `--json-schema` takes inline JSON wrapped in single quotes, and the argument list is
parsed line by line.

⚠️ **Two pins move together** — the consumer's `@ref` and `TEAM_REF` inside the workflow.
`ReleasePins` asserts it. This repo's own stub tracks `mainline` permanently and must stay there.

<!-- ─────────────────────────────────────────────────────────────────────────────
     REPO-OWNED BELOW THIS LINE. A resync from a newer template may replace the
     framing above; it must never touch what follows. These lessons exist nowhere
     else — losing them is permanent, unlike a stale instruction.
     ───────────────────────────────────────────────────────────────────────────── -->

## Lessons — append as you learn

⚠️ **This section is your memory, and updating it is part of the work, not an errand.** A local
session writes a durable lesson to its memory system; you write it here and commit it, or it
dies with the container. Add the evidence — the run id, the measurement, what it cost — because
a claim with no evidence gets edited away by whoever finds it inconvenient.

<!-- append entries here, newest last -->

**Some work simply cannot be done from here, and knowing which saves a wasted attempt.** The
GitHub MCP server has `get_label` but **no label write tool**; direct REST returns
`403 GitHub access is not enabled for this session`; there is no `gh`. So label re-syncs
(`ONBOARDING.md` §4) and board placement both need a local session. Say so and hand over the
command rather than improvising — the board number is 9.

⚠️ **Never pipe `git push` into `tail` in a retry loop.** `out=$(git push ...); rc=$?` — piping
makes `$?` the exit status of `tail`, so a failed push reports success and the loop breaks
happily. Measured: a push that had actually been rejected was reported `PUSH_OK`.

⚠️ **A merged branch is deleted on the remote, and the stale local ref then breaks the next
push.** `--force-with-lease` fails with `stale info` because `origin/<branch>` still points at the
merged tip. `git remote prune origin`, then push plain — there is nothing to force.

⚠️ **`git checkout <file>` discards every uncommitted change to it, not just the one you are
undoing.** Cost: a finished README section, written and never committed, wiped while restoring a
deliberately-injected typo. Commit before running destructive experiments; the container has no
other copy.

⚠️ **Prove a new test fails before trusting it.** A negative test that searched for a literal `—`
where the file stores `\u2014` changed nothing, so a live assertion looked inert. A check verified
only by "it passes" is a check you have not verified at all.

## Re-syncing this file

Compare **template-revision** above against `templates/CLAUDE_CLOUD.md` in
`matt-whitaker/claude-code`, and **SETUP revision** against its `SETUP.md`.

- Framing newer in the template → apply the changes above the repo-owned line. ⚠️ Merge, never
  copy over: the fill-ins and the lessons are this repo's, not the template's.
- SETUP.md newer → re-sync the facts per its Step 2, **including deleting** any that no longer
  exist there.
- Both current → say so and stop. Do not re-read either file to confirm what the numbers said.
