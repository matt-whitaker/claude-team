#!/usr/bin/env python3
"""Post-hook for any role that can file issues. Comments the attribution onto each issue the
run reported in its `filed` channel.

⚠️ AN ISSUE CANNOT SAY WHO FILED IT. Every role writes through the same App account, so the
author of a Security finding and of an Implementor's out-of-scope bug are indistinguishable —
and the issue carries no link back to the run, the task, or the story it came out of. What is
left is an issue nobody can place, in a backlog where placement is how work gets found.

⚠️ TIMING CANNOT RECOVER IT. Bracketing an issue against the runs in flight identifies the filer
only while exactly one role run is live; with several the answer is a guess. Driving concurrent
stories makes several the ordinary case, so the declaration is the mechanism and the bracket is
only a backstop.

Deterministic at both ends, the same shape as post-handoff.py: the schema forces the run to name
what it filed, this forces the attribution to land on it.

⚠️ It comments; it does not label. The kind label is the driver's, and applying the front-door
label here would start a run off another run's output — the chaining this package forbids.
"""

import json
import os

import team

REPORT = os.environ.get("REPORT", "")
ISSUE = os.environ.get("ISSUE", "")
STORY = os.environ.get("STORY", "")
ROLES = os.environ.get("ROLES", "").strip()
TRIGGER = os.environ.get("TRIGGER", "").strip()

MARKER = "<!-- claude-team:filed-by -->"

if not team.REPO:
    team.fail("REPO is required")

try:
    report = json.loads(REPORT) if REPORT.strip() else {}
except json.JSONDecodeError:
    # ⚠️ Not an error. A failed or skipped model step leaves this empty or malformed, and this
    # hook runs on `always()` precisely so a partial run still places what it managed to file.
    team.warn("no readable report — nothing to attribute")
    raise SystemExit(0)

filed = report.get("filed") if isinstance(report, dict) else None
if not filed:
    print("nothing filed by this run")
    raise SystemExit(0)

# ⚠️ Self-references are dropped rather than stamped: a role naming its own task or story would
# put an attribution comment on the very issue the run was triggered by.
skip = {str(n) for n in (ISSUE, STORY) if n}
who = ROLES or TRIGGER or "a role"

stamped = 0
for raw in filed:
    number = str(raw).lstrip("#").strip()
    if not number.isdigit():
        team.warn(f"filed entry {raw!r} is not an issue number — skipped")
        continue
    if number in skip:
        continue

    # ⚠️ `gh api` prints its error body to STDOUT, so a 404 reads as data to anything that only
    # checks for output. team.gh_json() parses only what exited zero.
    issue = team.gh_json("api", f"repos/{team.REPO}/issues/{number}")
    if not issue:
        team.warn(f"#{number} was reported as filed but cannot be read — not attributed")
        continue
    if issue.get("pull_request"):
        team.warn(f"#{number} is a pull request, not an issue — not attributed")
        continue

    origin = f"task #{ISSUE}" if ISSUE else f"PR #{ISSUE}" if not STORY else "this run"
    lines = [
        MARKER,
        f"**Filed by {who}**, during {origin}"
        + (f" of story #{STORY}" if STORY and STORY != ISSUE else "")
        + ".",
        "",
        "Reported by the run itself through its `filed` channel, so this attribution is the "
        "filer's own account rather than an inference from timing.",
        "",
        "⚠️ **No kind label is applied here.** Placing an issue is not starting it — the label "
        "is the maintainer's or the driving session's.",
    ]
    if team.upsert_comment(number, MARKER, "\n".join(lines) + team.run_footer()):
        stamped += 1
        print(f"attributed #{number} to {who}")
    else:
        team.warn(f"could not comment the attribution on #{number}")

kinds = [str(n) for n in filed]
print(f"filed this run: {', '.join('#' + k.lstrip('#') for k in kinds)} — attributed {stamped}")
