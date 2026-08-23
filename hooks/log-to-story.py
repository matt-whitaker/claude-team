#!/usr/bin/env python3
"""Keeps ONE rolling comment on a story listing its tasks in the order they should be
triggered, with what is done, what is ready, and what is waiting on something earlier.

Every task is triggered by hand, so "which one next" is a question the maintainer asks
constantly. log-to-epic answers it only for a story that sits under an epic; a standalone
story had no board at all.

NOTHING HERE IS WRITTEN BY A MODEL. Order is derived from two things the Architect must
produce for other reasons:

  phase   from the `Role:` stamp — the writer precedes the authors, which precede the tester
  number  within a phase, because it creates tasks in the order it intends them to run

A third stamp naming an order would be a third line it could skip. These two cannot be
skipped without breaking routing itself.
"""

import os

import team

STORY = os.environ.get("STORY", "")
MARKER = "<!-- claude-team:storylog -->"

if not team.REPO:
    team.fail("REPO is required")

if not STORY:
    print("No story in scope — nothing to order.")
    raise SystemExit(0)

tasks = team.sub_issues(STORY)
if not tasks:
    print(f"#{STORY} has no tasks — nothing to order.")
    raise SystemExit(0)


# ⚠️ ONE SOURCE FOR BOTH THE SORT AND THE SENTENCE THAT EXPLAINS IT. These were two
# independent statements of the same fact and they drifted: the caption read "authors, then
# tests, then docs" while `phase()` had put the writer FIRST, so it named the exact inversion
# the writer's position exists to prevent (#30). The caption is now built from this tuple, so
# there is nothing left to disagree with.
#
# ⚠️ Named for the ROLE STAMPS rather than the deliverables — "the writer", not "docs". The
# table printed directly above the caption has a role column showing `writer` and `tester`, so
# a reader matches the sentence to what they are looking at. "docs" also understates phase 1
# and quietly echoes the docs-come-last reading this defect was made of: the Writer's first
# deliverable is the product specification, and running before the authors is the whole point.
PHASES = ((1, "the writer"), (2, "the authors"), (3, "the tester"))
_RANK = {"writer": 1, "tester": 3}


def phase(role: str) -> int:
    """The writer first, then the authors, then the tester.

    ⚠️ The writer used to sort LAST. It moved because it owns the product specification, and a
    specification is only worth anything if it says what the code SHOULD do — which it cannot,
    if it was written by reading the code that already exists. Running first is what makes
    "from intent, not from the diff" true by construction rather than by instruction.

    An unstamped task sorts with the authors — routing defaults it to an author too, so the two
    stay consistent.
    """
    return _RANK.get(role, 2)


rows = []
for task in tasks:
    role = team.role_stamp(team.issue_body(task["number"]))
    rows.append(
        {
            "phase": phase(role),
            "number": task["number"],
            "state": task.get("state", ""),
            "role": role or "—",
            "title": task.get("title", ""),
        }
    )
rows.sort(key=lambda r: (r["phase"], r["number"]))

# Ready/waiting falls out of the same order rather than being tracked separately: a task is
# ready when everything before it is closed. So the first open task IS the one to trigger.
nxt = next((r for r in rows if r["state"] == "open"), None)

lines = [MARKER, "## Tasks, in trigger order", ""]
if nxt:
    lines += [
        f"**Trigger next — #{nxt['number']}**  ",
        f"{nxt['title']}  ",
        f"`Role: {nxt['role']}`",
        "",
    ]
else:
    lines += ["_Every task is closed — the story is ready to review._", ""]

lines += ["| | task | role | state |", "|---|---|---|---|"]
for row in rows:
    if row["state"] == "closed":
        mark = "✅ done"
    elif nxt and row["number"] == nxt["number"]:
        mark = "⬜ **ready**"
    else:
        mark = "⏸ waiting"
    lines.append(f"| {row['phase']} | #{row['number']} {row['title']} | `{row['role']}` | {mark} |")

lines += [
    "",
    # Derived, never restated — see PHASES.
    "Order is derived — "
    + ", then ".join(name for _, name in PHASES)
    + "; by issue number within each.",
    "Rewritten automatically whenever a task changes state.",
]

if team.upsert_comment(STORY, MARKER, "\n".join(lines) + "\n" + team.run_footer()):
    print(f"updated the task order on story #{STORY}")
else:
    team.warn(f"could not update the task order on #{STORY}")
