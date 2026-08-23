# CLAUDE_CLOUD.md — what is true about THIS repo

⚠️ **Everything portable moved to `claude-harness`.** The environment facts a cloud session needs —
no `~/.claude/`, an ephemeral container, no `gh`, only attached repos reachable, the git traps that
cost something — now live in `.claude/rules/claude-harness.md`, which loads automatically in every
session here, cloud **and** local. This file is only what is true about *this repo*.

⚠️ **Mention it in backticks, never as an unbackticked `@path`.** An `@path` in a `CLAUDE.md` is a
real, unconditional import.

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

⚠️ **A cloud session has no memory, so a lesson lives here or dies with the container.** Add the
evidence — the run id, the measurement, what it cost — because a claim with no evidence gets edited
away by whoever finds it inconvenient.

⚠️ **If the lesson would be true in any repo it belongs in `claude-harness`, not here.** That is the
rule that stops the layers mixing again, and it is easiest to break when writing something down in a
hurry. Four git lessons were moved out of this file for exactly that reason.

<!-- append entries here, newest last -->

**Label writes and board placement need a LOCAL session.** The general fact — the GitHub MCP server
has `get_label` and no label write, and direct REST is refused — is in the harness rule. What is
specific here: that makes `ONBOARDING.md` §4's label loop and board placement impossible from a
cloud session. Say so and hand over the command rather than improvising. **The board is 9.**

## Re-syncing

The harness rule carries its own `harness-rule-revision`; compare it against
[`matt-whitaker/claude-harness`](https://github.com/matt-whitaker/claude-harness) and **replace the
file** if it is behind. There is nothing to merge — none of it is this repo's.

⚠️ This file has no revision and needs none. Everything in it is this repo's own, so nothing
upstream can make it stale.
