#!/usr/bin/env python3
"""The back half of the sandwich: scripted checks on what a run left behind.

⚠️ WHY THIS RUNS AFTER RATHER THAN BEFORE. Every check here is unanswerable at the front and
trivial at the back. "Does this story have tasks?" reads 0 for *every* story at branch-creation
time, because `ensure-story-branch.py` runs before `file-sub-issues.py`. "Was this branch ever
used?" is not knowable until work lands, or does not. "Did the Architect deliver?" is only knowable
once it has stopped. Attempts to answer these early produced fragile logic; observing them late is
simply cheaper.

⚠️ SCRIPTED, WITH NO MODEL STEP IN ITS JOB, and that is what lets its job hold `contents: write`.
Nothing untrusted executes there. The routing phase at the front consults the model only where the
script has no answer; this half has no such case yet, and wiring one that decides nothing would be
a channel with no reader.

TWO MODES, because the two checks become true at different moments:

  MODE=deliverable  did the role leave the artifact it exists to produce?

(The kinds sweep moved to labels-and-status.py MODE=kind; branch creation moved to
branch-navigation.py, which runs after file-sub-issues.py where the has-tasks question is
answerable at last.)

⚠️ NOTHING HERE DELETES. An earlier version swept branches that nothing had used; the branches
should not have been created, and here they are not. Putting the decision where the knowledge is
removes the need for a destructive capability rather than justifying one.
"""

from __future__ import annotations

import os

import team

MODE = os.environ.get("MODE", "")
ISSUE = os.environ.get("ISSUE", "")
ROLE = os.environ.get("ROLE", "")
KIND = os.environ.get("KIND", "")

if not team.REPO:
    team.fail("REPO is required")


def check_deliverable() -> None:
    """An Architect that produced no `Branch:` line has stalled — and reports success.

    ⚠️ MEASURED TWICE, on #834 and #866: ~6 turns, ~30s, no error, no denials, nothing written,
    and a green run. Both recovered on a plain re-trigger, so the input was never the problem.
    `ensure-story-branch.py` already says exactly the right thing about it — as a `::warning::`,
    which fails nothing and nobody reads. This is the same sentence with teeth.

    ⚠️ An epic and a spike legitimately have no branch. They must not fail here.
    """
    if ROLE != "architect" or not ISSUE:
        return
    if KIND in ("epic", "spike"):
        print(f"#{ISSUE} is {'an epic' if KIND == 'epic' else 'a spike'} — no Branch line expected.")
        return

    if team.branch_line(team.issue_body(ISSUE)):
        print(f"#{ISSUE} carries its Branch line — the Architect delivered.")
        return

    team.fail(
        f"#{ISSUE} has no Branch line after the Architect ran, so the story cannot be worked: "
        "every role that follows reads that line to know where to commit. This is the stall that "
        "reports success — re-add the label to run it again."
    )


if MODE == "deliverable":
    check_deliverable()
else:
    team.fail(f"MODE must be 'deliverable', got {MODE!r}")
