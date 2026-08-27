# claude-team

**team-ref: v4.3** · from `matt-whitaker/claude-team`

⚠️ **This file is entirely claude-team's.** Nothing repo-specific goes in it. To upgrade, **replace
it** — never merge. To uninstall, delete it.

⚠️ **`team-ref` must equal the `uses:` pin in `.github/workflows/claude.yml`.** They are one fact
in two places — which version of the team this repo runs. A mismatch is a half-done upgrade, and it
is the only part of one a clone can detect on its own.

⚠️ **This is what a SESSION needs. The roles do not read it.** A role running inside a workflow is
given `prompts/_shared.md` + `prompts/<role>.md`, fetched at the pin. Role-scoped instruction never
belongs here: a rule scopes by file path, never by who is running.

## What is installed

| | |
|---|---|
| `.github/workflows/claude.yml` | the stub — triggers, inputs, and the `uses:` pin, the only pin you hold |
| `.claude-team/prompts/` | your overlays. `_shared.md` required, `<role>.md` optional |
| `.claude-team/setup.sh` | optional, executable |
| `.claude/rules/claude-team.md` | this file |

## The issue hierarchy

| level | branch | its PR targets | closed by |
|---|---|---|---|
| **Epic** | none | — | its stories closing |
| **Spike** | none | — | the maintainer, once they have decided |
| **Story** | `<story#>-<summary>`, named by the Architect | the **default** branch | its PR merging |
| **Task** | none of its own — its work lands on the story's branch | — | a hook, once its work has landed |

⚠️ **A task has no PR, and there is exactly one PR per story.** Its absence before the last task
closes is the design, not a failure.

⚠️ **An unprocessed issue is a STORY.** An epic has to say so — an `epic` label, or a title
beginning "Epic". Having sub-issues does not make one: a story has those too, they are its tasks.

## Starting a run

- **A label on an issue is the front door.** Applying it starts a run, and a script picks the role
  from the issue's state. ⚠️ **Applying it is the maintainer's gesture, and the exception is
  named**: a session handed a whole story drives that story, which means labelling its waves. That
  is the whole of it — outside a story it was handed, a session does not label an issue to make
  something happen.
- The same handle in a **comment** does the same. `@claude/<role>` names the role outright and
  skips the inspection.
- ⚠️ **A run executes the hooks and prompts at the PIN, never from this clone.** Editing your
  overlays on a branch changes nothing about the run editing them.

## Where work goes

⚠️ **Work goes on the branch of the thing the run was triggered on** — not a branch a model picks.
An issue trigger means a fresh task branch and one PR at the story level; a PR trigger means
commits on that PR's branch and no new PR.

## What this file does not carry

Everything else lives in [`claude-team`](https://github.com/matt-whitaker/claude-team) — its
`CLAUDE.md`, its install runbook, its prompts and its hooks. Read it there. ⚠️ **Nothing here
summarises them**: a copy drifts, and the copy is what gets read.
