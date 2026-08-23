# claude-harness

**harness-rule-revision: 2** · from `matt-whitaker/claude-harness`

⚠️ **This file is entirely claude-harness's.** Nothing repo-specific goes in it. To upgrade,
**replace it** — never merge. To uninstall, delete it. What this repo knows about itself lives in
its own `CLAUDE.md`.

## Which environment am I?

```bash
env | grep -E 'CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE|CLAUDE_CODE_CONTAINER_ID|CLAUDE_CODE_REMOTE_SESSION_ID'
```

Anything set → **cloud session**. Nothing set → **local**. ⚠️ Decide from the variables, not by
probing for a memory tool: the variables are free and deterministic, a missing tool is the
confirmation rather than the trigger.

## If you are a cloud session

- **Nothing under `~/.claude/` reaches you** — no auto memory, no user `CLAUDE.md`, no personal
  skills. This file does, because it is committed to the repo.
- **The container is ephemeral.** Anything not committed and pushed is lost, including anything
  you learn. Write a durable lesson into a committed file, or it dies with the container.
- Repos live under `/home/user/`. **There is no `gh` CLI** — GitHub is reached through MCP tools,
  and direct REST is refused.
- **Only attached repos are reachable.** Another must be attached before you can read it, even to
  answer a question about it. Check what is available before reporting anything inaccessible.
- ⚠️ **Some work simply cannot be done from here.** Label writes are the known case: the MCP
  server has `get_label` and no write. Say so and hand over the command rather than improvising.
- You may arrive **already pinned to a branch** for session coherence. Prefer it over any naming
  convention, and say so rather than silently renaming.

## Working with the maintainer

- **Secrets never pass through a session.** They paste values into the GitHub or console UI; your
  job is to say exactly *which* values and *where* they go.
- **Destructive and outward-facing work waits for an explicit instruction** — merging,
  force-pushing, deleting, anything beyond opening a PR. Approval in one context does not extend
  to the next.
- **Report what actually happened.** Failed tests get quoted. A skipped step gets said. Finished
  and verified gets stated plainly without hedging. ⚠️ A message telling someone not to look
  further is the most expensive thing you can write.

## Craft — each of these cost something measured

- **Never pipe `git push` in a retry loop.** `git push ... | tail` makes `$?` the exit status of
  `tail`, so a **rejected push reports success**. Use `out=$(git push ...); rc=$?`.
- **A merged branch is deleted remotely,** and the stale local ref then breaks the next push —
  `--force-with-lease` fails `stale info`. `git remote prune origin`, then push plain.
- **`git checkout <file>` discards every uncommitted change to it,** not only the one being
  undone. Cost: a finished section wiped while reverting a one-character typo.
- **Prove a new test fails first,** against the unfixed code, for the reason you expect. A check
  verified only by passing is not verified.
- **`value or default` swallows the empty case** — empty dict, empty list, `0`, `""`. When empty
  is what you are testing, use a sentinel.

## claude-team, if this repo has it

`claude-team` is the GitHub-agent orchestration, installed separately into `.claude-team/` and
`.github/`. You will be asked to **act on** it — investigate a failed run, diagnose a workflow
failure, repair what the custodian could not, trigger a workflow, open a PR to move a story along.
Do that.

⚠️ **Read how it behaves from `claude-team` itself** — its `CLAUDE.md`, `ONBOARDING.md` and its
prompts are the source. Nothing here summarises them, and nothing here should: a copy drifts, and
the copy is what gets read.

⚠️ **The split is by whose behaviour a fact describes.** A fact about *the session* is this file's,
even while working on the team. A fact about *the team* is the team's, even though a session is
what reads it.

## If you suspect this file did not load

⚠️ **The most likely cause is a hook in the wrong scope, not a broken rule.** `/context` lists what
actually loaded under **Memory files** — check there first rather than inferring from behaviour.

An `InstructionsLoaded` hook logs every instruction file and why it loaded. ⚠️ **It only works in
`~/.claude/settings.json`.** A hook in a project's `.claude/settings.json` does **not** run in a
folder whose workspace-trust dialog has not been accepted, and a `-p` session never counts as
accepting it — so a project-scoped hook that silently never fires reads exactly like a rule that
never loaded. Setup for it is in `claude-harness`'s `SETUP.md`.

⚠️ **Compaction is not the explanation.** These files reload after a `/compact` — `compact` is one
of the hook's own `load_reason` values.

## Where a durable lesson goes

A local session writes it to memory. A cloud session **commits it** — to this repo's own
`CLAUDE.md`, or wherever this repo keeps them. ⚠️ **If the lesson would be true in any repo it
belongs upstream in `claude-harness`, not here** — that is the rule that stops the layers mixing
again, and it is easiest to break when writing something down in a hurry.
