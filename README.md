# claude-team

> **See it live:** [claude-team-example](https://github.com/matt-whitaker/claude-team-example) — the smallest real integration, and this repo's own drill target. Its Actions tab shows the machinery running (and stopping, by design, at the missing-credentials boundary).

A portable definition of a Claude/GitHub role team — the prompts each role runs on, and the
scripted hooks that do the bookkeeping around them. A repo **consumes** it by pointing a
workflow at these files, and **extends** it with its own per-role overlay.

## Entry points

- [`prompts/`](prompts/) — [`_shared.md`](prompts/_shared.md) for every role, plus one file
  per role. A role's prompt is the shared file, then its own, then the consumer's equivalents.
- [`hooks/`](hooks/) — the scripted steps that run around each model step, in Python. Each
  explains itself in its own docstring; [`team.py`](hooks/team.py) holds what they share.
- [`schemas/`](schemas/) — the machine-readable contracts. A role carrying one must return JSON
  matching it, and a hook does something with the result:
  [`handoff.json`](schemas/handoff.json) is what one author passes to the next,
  [`findings.json`](schemas/findings.json) what a Researcher returns from a spike,
  [`route.json`](schemas/route.json) the role the root role picks when routing could not decide,
  and [`repairs.json`](schemas/repairs.json) the process repairs it wants applied.

## The model

Work is **epic → story → task**. An epic is a grouping and has no branch. A story owns a
branch and a PR against the default branch. A task owns a branch cut off the story's and a PR
back into it — merging that closes the task, and the story's PR accumulates the lot.

A **spike** sits outside that shape: a question nobody has answered yet, with no branch, no PR
and no children. It is not a small story — there is nothing to decompose until it is answered.

Eight roles. One runs per trigger, and nothing chains: no role starts another, and a person
triggers every run.

| role | picked up from | writes |
|---|---|---|
| `@claude` | its name in a comment, and any route the script could not settle | an answer, a role name, and repairs to process state — it is who you talk to |
| Architect | an epic, or an unshaped story | the issue, a story's branch, and its tasks |
| Researcher | a spike | findings and a recommendation, appended to the issue — it holds no shell |
| Implementor | a task stamped `Role: implementor` | code, outside the design system |
| Designer | a task stamped `Role: designer` | code, inside the design system |
| Tester | a task stamped `Role: tester` | tests |
| Writer | a task stamped `Role: writer`, run **first** | the product specification, then documentation |
| Security | every merge, and on request | issues it files |

## How a run is routed

**Routing is a script first: state decides wherever state can, and a model is consulted only where it cannot — a bare mention that could be a question or a request, a stamp that is missing — with the script's own answer as the floor when the consultation fails.** It is all readable state, and the one judgement call —
which author owns a task — is answered once by the Architect and written into the task as a
`Role:` line. Three ways in:

- **The front-door label on an issue** starts a run, and the router reads the issue's state to
  pick the role. This is the usual path, and re-applying the label is the "run again" gesture.
- **A `@claude/<role>` handle in a comment** names a role outright and skips the inspection —
  the way to override a bad guess, on an issue or a PR.
- **Naming the root role in a comment** with no handle is a conversation. It answers rather than
  starting work.

Where the state that should decide is **missing** — a task with no `Role:` stamp, say — the router
falls back to a default rather than stalling, but that default is a floor, not the decision: it
asks the root role first and runs the fallback only if that cannot answer. Either way the run says
on the issue that it did not route from state alone, and what one-line change would make it
deterministic next time.

## Consuming it

The consumer contract is a ~60-line stub calling the reusable workflow
([`templates/consumer-stub.yml`](templates/consumer-stub.yml), pinned to a `vN` tag) plus a
`.claude-team/` directory holding your prompt overlays. [`ONBOARDING.md`](ONBOARDING.md) is the
runbook — point a Claude session at it together with a target repo and it walks the whole
install: inputs, stub, overlays, labels, the maintainer's secrets, and the drill that proves it.
[`claude-team-example`](https://github.com/matt-whitaker/claude-team-example) is a living,
annotated install.

Nothing in this package names a consuming repo, its branches, its gate or its packages — anything
that does belongs in your overlay.

See [`CLAUDE.md`](CLAUDE.md) for the design decisions, the platform constraints they work
around, and the failures that shaped them.
