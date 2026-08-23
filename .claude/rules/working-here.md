# Working in claude-team

⚠️ **Facts about THIS repo that a session cannot derive from the code.** How a Claude Code session
works in general is not here — that is `claude-harness.md` beside this file, which every repo gets.
If something you are about to write down would be true in another repo, it belongs there.

## How work ships here

- Default branch: `mainline` — **not** `main`.
- Verification gate: `python3 -m unittest discover -s tests`. Stdlib only, no dependencies,
  runs anywhere. ⚠️ It is the gate — a change that has not run it is not finished.
- Board: **9** (Claude Team). ⚠️ You cannot reach it; see *Lessons*.
- Branch naming: `<issue#>-<kebab-summary>`, unless the session arrived pinned to one.

⚠️ **A session may arrive already pinned to a branch** it should stay on, for session
coherence. Prefer that branch over the naming convention, and say so rather than silently renaming.

## Hazards particular to this repo

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

## Lessons — append as you learn

⚠️ **A cloud session has no memory, so a lesson lives in a committed file or dies with the
container.** Add the evidence — the run id, the measurement, what it cost — because a claim with no
evidence gets edited away by whoever finds it inconvenient.

⚠️ **If the lesson would be true in any repo it goes upstream to `claude-harness`, not here.**
Keeping one local makes it invisible to every other repo that would hit the same trap.

<!-- append entries here, newest last -->

**Label writes and board placement need a LOCAL session.** `ONBOARDING.md` §4's label loop and
board placement cannot be done from a cloud session — say so and hand over the command rather than
improvising. **The board is 9.**
