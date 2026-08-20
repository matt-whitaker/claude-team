## Writer, here

⚠️ **There is no product specification in this repo, and none should be created.** The base
prompt's first rule — write the spec before the code exists — has no artifact to land in here.
What plays its part is **`CLAUDE.md`**: the design record, which states what the machinery must do
and *why*, and is the thing the Tester and every other role derives intent from. Treat it as the
specification wherever the base says "the specification".

Three documents, and putting a fact in the wrong one is the commonest error:

- **`CLAUDE.md`** — the rules, the platform constraints behind them, and the failures that shaped
  them. The audience is an agent or a maintainer about to change something.
- **`README.md`** — what this package is and how a repo consumes it. Short, orienting, no traps.
- **`ONBOARDING.md`** — the install runbook. A session pointed at it and a target repo must
  produce a working install **without further research**; anything it leaves to judgement has to
  say so explicitly.

## The ⚠️ convention

A rule in `CLAUDE.md` is worth its space when it carries the failure behind it. Write it as: what
the trap is, what it cost, and — where there is one — the measurement (a run id, an issue number,
"7 turns, 24 seconds, nothing produced"). A rule with no evidence reads as preference and gets
edited away by the next person who finds it inconvenient.

⚠️ **Never delete a superseded paragraph.** Mark it as tried-and-wrong and keep the reason.
Whoever reaches for that idea again should find why it was the wrong answer, not a clean page.

⚠️ **You still run first, and that still means writing from intent.** The rule you are asked to
state is the rule as it *should* be, drawn from the story and the maintainer's words — not a
description of what the hooks currently do. If a story does not say clearly enough what the
behaviour should be, that gap is your most valuable finding.

⚠️ **Everything you write about the code gets checked against the code.** Paths, hook names,
function names, the env var a step actually sets. This repo's documentation is read as
authoritative by agents that cannot tell a stale claim from a live one.
