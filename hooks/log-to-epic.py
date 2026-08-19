#!/usr/bin/env python3
"""Keeps ONE rolling work-log comment on an epic, so the maintainer can see the state of the
whole epic in one place and decide what to assign next — without opening every story.

FULLY DERIVED. Nothing here is written by a model. Which issue ran, which roles ran, what is
still open and what comes next are all readable from GitHub, so none of it can be skipped or
misreported. The opposite shape is what this repo keeps being bitten by: sub-issue filing
asked the deciding role to leave a machine-readable manifest, and across nine epics it wrote
one exactly once.

ONE COMMENT, REWRITTEN — not one per run. An epic with ten tasks and three roles each would
otherwise accumulate thirty comments. The status table is rebuilt from live state every time,
so it is never stale; only the Recent lines accumulate, and they are capped.

NO EPIC IS A NORMAL OUTCOME. A story here need not sit under one, and when it does not there is
nothing for this hook to say — log-to-story covers that case on the story itself. See resolve().
"""

from __future__ import annotations

import datetime as dt
import os
import re

import team

ISSUE = os.environ.get("ISSUE", "")
ROLES = os.environ.get("ROLES", "").strip()
PR = os.environ.get("PR", "")
MARKER = "<!-- claude-team:worklog -->"
KEEP = 12

if not team.REPO:
    team.fail("REPO is required")

if not ISSUE:
    print("Not triggered on an issue — no epic to log against.")
    raise SystemExit(0)

def resolve(number: str) -> tuple[str, str] | None:
    """Which story and which epic this issue belongs to, or None when there is no epic.

    ⚠️ THE EPIC IS IDENTIFIED BY ASKING, NEVER BY ABSENCE OF A PARENT. This walked up until an
    ancestor had no parent and called that the epic, which is right for a story sitting under
    one and wrong for a task whose story has no epic at all — and the two arrive identically,
    as "an issue whose parent has no parent". A parentless story therefore read as an epic and
    its own tasks read as stories: a work log landed on #537 listing #538 and #539 under a
    "Stories" heading, telling the maintainer the Architect would shape a task already stamped
    Role: writer.

    The same assumption was removed from story_from_branch in #502 and survived here.
    """
    parent = team.parent(number)
    if not parent:
        print(f"#{number} has no parent — an epic itself, or unparented work. Nothing to log.")
        return None

    if team.is_epic(parent):
        return number, parent

    story = parent
    grandparent = team.parent(story)
    if not grandparent:
        print(f"story #{story} sits under no epic — nothing to log. (log-to-story covers it.)")
        return None

    # An ancestor two levels up is where an epic belongs. If it does not say it is one, warn
    # rather than assume: silence would hide a mislabelled epic, and assuming is this bug.
    if not team.is_epic(grandparent):
        team.warn(
            f"#{grandparent} is where #{number}'s epic should be, but carries neither the "
            f"'{team.EPIC_LABEL}' label nor an 'Epic' title, so nothing was logged. Mark it if "
            "it is one."
        )
        return None

    return story, grandparent


resolved = resolve(ISSUE)
if not resolved:
    raise SystemExit(0)
STORY, EPIC = resolved

print(f"logging #{ISSUE} (story #{STORY}) against epic #{EPIC}")


def first_open(number: str, exclude: str) -> dict | None:
    return next(
        (k for k in team.sub_issues(number)
         if k.get("state") == "open" and str(k["number"]) != str(exclude)),
        None,
    )


# The next open task of the story just worked; failing that, the next open story of the epic.
# Named with its Role stamp so the maintainer can act on it without opening it.
nxt, scope, kind = first_open(STORY, ISSUE), f"task of story #{STORY}", "task"
if not nxt:
    nxt, scope, kind = first_open(EPIC, STORY), f"story of epic #{EPIC}", "story"

if not nxt:
    next_line = "_Nothing open — the epic looks complete._"
else:
    if kind == "task":
        # Only a TASK carries a `Role:` stamp — it is what routes an author to it. A story is
        # shaped by the Architect and has no stamp by design, so demanding one there would be
        # a standing false alarm on every epic.
        role = team.role_stamp(team.issue_body(nxt["number"]))
        note = (
            f", stamped `Role: {role}`" if role
            else ", **no `Role:` stamp** — the Architect should add one"
        )
    else:
        note = " — label it `@claude` and the Architect will shape it"
    next_line = f"**#{nxt['number']} — {nxt.get('title','')}**  \nnext open {scope}{note}"

def landed(number: str | int) -> str:
    """Whether a story's work is actually IN the default branch, which is not the same question
    as whether its tasks are closed.

    ⚠️ THIS COLUMN EXISTS BECAUSE THE TASK COUNT WAS READ AS "DONE". An epic showed
    `#602 … | ⬜ open | 2/2` — every task closed — while its PR was still open, so the props a
    dependent story needed existed on no branch that story could see. The dependent story was
    started anyway and its Tester found nothing to test. Task completeness and landedness are
    different facts; only one of them was on the board.

    Derived from the story's own Branch line and GitHub's PR state — never from prose.
    """
    branch = team.branch_line(team.issue_body(number))
    if not branch:
        return "no branch"
    prs = team.gh_json(
        "pr", "list", "--repo", team.REPO, "--head", branch, "--state", "all",
        "--json", "number,state",
    ) or []
    if not prs:
        return "no PR yet"
    pr = prs[0]
    return f"PR #{pr['number']} {(pr.get('state') or '').lower()}"


table = ["| story | state | tasks | landed |", "|---|---|---|---|"]
for story in team.sub_issues(EPIC):
    kids = team.sub_issues(story["number"])
    if not kids:
        counts = "—"
    else:
        done = sum(1 for k in kids if k.get("state") == "closed")
        open_ns = " ".join(f"#{k['number']}" for k in kids if k.get("state") == "open")
        counts = f"{done}/{len(kids)}" + (f" · open: {open_ns}" if open_ns else "")
    mark = "✅" if story.get("state") == "closed" else "⬜"
    table.append(
        f"| #{story['number']} {story.get('title','')} | {mark} {story.get('state','')} "
        f"| {counts} | {landed(story['number'])} |"
    )

# carry the previous Recent lines forward
previous: list[str] = []
comments = team.gh_json("api", f"repos/{team.REPO}/issues/{EPIC}/comments", "--paginate") or []
for comment in comments:
    if MARKER in (comment.get("body") or ""):
        after = re.split(r"^### Recent", comment["body"], maxsplit=1, flags=re.M)
        if len(after) > 1:
            previous = [l for l in after[1].splitlines() if l.startswith("- ")]

entry = (
    f"- `{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')}` "
    f"**#{ISSUE}** {team.issue(ISSUE, 'title').get('title','')} — {ROLES or '（unknown）'}"
    + (f" · PR #{PR}" if PR else "")
)
recent = ([entry] + previous)[:KEEP]

body = "\n".join(
    [
        MARKER,
        "## Work log",
        "",
        "Rebuilt automatically after every authoring run. Status is read live from the",
        "issues, so it is current as of the newest entry below.",
        "",
        "### Next up",
        "",
        next_line,
        "",
        "### Stories",
        "",
        *table,
        "",
        "### Recent",
        "",
        *recent,
    ]
) + "\n"

if team.upsert_comment(EPIC, MARKER, body + team.run_footer()):
    print(f"updated the work log on epic #{EPIC}")
else:
    team.warn(f"could not update the work log comment on epic #{EPIC}")
