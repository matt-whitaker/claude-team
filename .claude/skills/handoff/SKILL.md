---
name: handoff
description: Write a handoff brief for another Claude session — when work crosses into a different repo, or a finding belongs to a codebase this session is not set up for. Produces raw markdown the maintainer carries over, built so the receiving session can falsify the premise before acting on it.
argument-hint: [target repo or task]
---

A session cannot talk to another session. The maintainer carries the brief, so it has to stand
on its own.

## Before writing

Establish what the receiving session must check first, and what evidence you actually hold —
paths with line numbers, commands and their real output, run ids, measurements. Anything you
assert without evidence, mark as unverified rather than dropping it.

## Structure

1. **Header** — from, to, scope, and the single file or area in play. State up front if no
   change is wanted in the sending repo.
2. **Verify the premise** — the file, command or state the receiving session checks *before*
   acting, and what to do if it turns out to be wrong. Say "declare this void and report back"
   explicitly. ⚠️ A handoff that cannot be falsified by its reader is just an instruction to
   comply.
3. **The finding, with evidence** — the conclusion *and* what grounds it, so the reader can
   catch an error rather than inherit it, and never re-derives what you already paid for.
4. **The change to make** — bounded. Name what belongs to a different repo or a different
   decision.
5. **What NOT to do** — including known-and-accepted gaps it will notice and should not re-file
   as discoveries.
6. **Ship discipline for the target repo** — issue, branch, gate, PR body, board.
7. **What could not be determined** — and why. Never drop this section.

## Hazards

⚠️ Where the target repo runs an agent workflow, a literal front-door handle in an issue or PR
comment starts a real run, and backticks do not protect it. Write around it, and say why, so
the receiving session inherits the discipline.

⚠️ Do not send a summary. Send what the session needs to act and to disagree.

## Deliver

Write it to a markdown file and hand over the path. Offer to publish it as an artifact with a
copy button when the maintainer will move it by hand — raw markdown, never rendered, because
rendered output is not what a session reads.

<!-- skill-revision: 3 — from matt-whitaker/claude-team/skills/handoff.
     Bumps only when THIS skill changes, never because SETUP.md did.
     Reinstall per SETUP.md §Skills: copy into the consuming repo's .claude/skills/. -->
