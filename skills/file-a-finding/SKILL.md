---
name: file-a-finding
description: File something you found — a bug, a security finding, a wrong rule, a defect out of scope — as an issue a fixer can act on without re-doing the investigation. Use when work surfaces a problem that is not the work you were asked to do, in any repo running claude-team.
argument-hint: [what you found]
---

A finding is filed, never swept into the current change: scope grows by surfacing follow-ups. And
the report is the deliverable — the Architect that shapes a bug **may not rewrite its body**, so
whatever you write is the only grounding the fixer gets. A thin report is not repaired downstream;
it is rejected as unusable.

## 1. Decide what it is

| it is | when | where it goes |
|---|---|---|
| **bug** | something behaves wrong and you can say how | `bug` label; one branch, one PR, usually one task |
| **security finding** | a boundary is reachable that should not be | `bug` label; the ceiling stated (see below) |
| **spike** | you found a question, not an answer | `Spike:` title or `spike` label — no branch, ships nothing |
| **a rule that is wrong** | the code is right and the instruction is not | the repo owning the rule, naming the rule and what it cost |

⚠️ **If you cannot state a reproduction or a measurement, it is a spike, not a bug.** Filing an
unmeasured hunch as a bug hands a fixer nothing to work from.

## 2. Establish it in the repo that owns it

⚠️ **The repo that owns the fix, not the one where you noticed it.** A workflow defect noticed in a
consumer belongs to the engine; a data defect noticed by the engine belongs to the data repo.
⚠️ `Closes owner/repo#N` does not fire across repositories — cross-repo trackers get closed by hand,
so prefer one issue in the owning repo over a pair.

## 3. Write what a fixer needs

- **What is wrong**, stated so a reader can check it rather than take it on trust. Name what you
  looked at: paths with line numbers, run ids, the command and its real output.
- **The reproduction** — the shortest path from a clean state to the wrong behaviour.
- **The measurement** — how often, how long, how many. "Twice in one story, both inter-wave
  transitions" is actionable; "sometimes" is not.
- ⚠️ **What you could NOT determine.** The section under the most pressure to skip and the most
  valuable to keep — without it the next person re-derives the gap without knowing it was one.
- **The ceiling**, for anything security-shaped: what it actually reaches, and what it does not.
  A finding that overstates its blast radius gets discounted; one that understates it gets ignored.
- **The fix you would make**, if you have one — as a proposal, marked as such. Naming the wrong fix
  is often worth more than naming the right one.

⚠️ **Evidence, not a wishlist.** A body that argues for a solution instead of describing a problem
leaves the fixer no way to disagree with the diagnosis.

## 4. Shape it for the engine, then stop

- Create it **unlabelled except for the kind** (`bug` / `spike`). The front-door label is the
  maintainer's gesture — filing is not starting.
- **No `Branch:` or `Role:` lines.** Those are the Architect's to write; a body carrying them is a
  task, and `team.kind()` will read it as one.
- Prefer **one task** when it is shaped later: a bug is a fix, not a decomposition.
- ⚠️ **Do not fix it in the current change.** Say in your report that you filed it, with the link.

## Conduct

- ⚠️ **Fix and report, never fix quietly** — where a repair is yours to make, the finding still gets
  written down. Breakage that is visible is what produces the rule that prevents it.
- **A repeat is not a re-file.** If the same finding already exists, add the new measurement to it;
  a second issue splits the evidence.
- **File it even when it is your own defect.** Especially then.
