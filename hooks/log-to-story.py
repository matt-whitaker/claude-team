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


def phase(role: str) -> int:
    """The writer first, then the authors, then the tester.

    ⚠️ The writer used to sort LAST. It moved because it owns the product specification, and a
    specification is only worth anything if it says what the code SHOULD do — which it cannot,
    if it was written by reading the code that already exists. Running first is what makes
    "from intent, not from the diff" true by construction rather than by instruction.

    An unstamped task sorts with the authors — routing defaults it to an author too, so the two
    stay consistent.
    """
    return {"writer": 1, "tester": 3}.get(role, 2)


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
    "Order is derived — authors, then tests, then docs; by issue number within each.",
    "Rewritten automatically whenever a task changes state.",
]

if team.upsert_comment(STORY, MARKER, "\n".join(lines) + "\n" + team.run_footer()):
    print(f"updated the task order on story #{STORY}")
else:
    team.warn(f"could not update the task order on #{STORY}")
