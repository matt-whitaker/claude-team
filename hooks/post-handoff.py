#!/usr/bin/env python3
"""Post-hook for the authoring job. Puts the author's JSON handoff on the STORY'S ISSUE, as
one marked comment per task, so a later role can read it.

The schema was never the broken half. `--json-schema` forces the author to emit both keys,
so `[]` stays distinguishable from "forgot". What failed is that `structured_output` is a
STEP output: it dies with the job, and the Tester and Writer now run as their own tasks.
Only the transport lives here; the guarantee is unchanged.

The issue, not the story's PR: under sub-branching the story branch is empty until the first
task PR merges into it, so its PR does not exist while the first author is running.

Deterministic at both ends, which is what separates this from asking a model to leave a
machine-readable block behind — the schema forces production, this forces delivery.
"""

import os

import json

import team

HANDOFF = os.environ.get("HANDOFF", "")
ISSUE = os.environ.get("ISSUE", "")
PR = os.environ.get("PR", "")
STORY = os.environ.get("STORY", "")
ROLES = os.environ.get("ROLES", "").strip()

if not team.REPO:
    team.fail("REPO is required")

if not HANDOFF:
    print("No handoff to post — no author ran, or its step failed.")
    raise SystemExit(0)

# ⚠️ A PR FOLLOW-UP MUST REACH THE STORY, and for a long time it did not. This read
# `if not ISSUE: exit` — and the workflow blanks ISSUE on a PR trigger — so the hook returned
# before it ever looked at STORY, which `delegate.py` rule 2 had already resolved from the PR's
# head branch. The run carrying the maintainer's review feedback therefore produced a
# schema-forced handoff and dropped it on the floor. That is how the decision to delete
# `nextIncompleteEquipment` (#626) reached nothing durable and was rebuilt two PRs later (#651).
target = STORY or ISSUE
if not target:
    team.warn(
        "no story and no issue — nowhere to attribute this handoff. A hand-cut branch with no "
        "issue prefix resolves to no story; name the branch <story#>-<summary> so it does."
    )
    raise SystemExit(0)

source = f"#{ISSUE}" if ISSUE else f"PR #{PR}" if PR else "an untraceable trigger"

try:
    parsed = json.loads(HANDOFF)
except json.JSONDecodeError:
    parsed = {}

# ── the decisions log: appended, never replaced ─────────────────────────────────────────
#
# ⚠️ THIS ONE APPENDS, and the other upserts. A handoff is a snapshot for the next role and is
# regenerated whole each run, so replacing it loses nothing. A decision is a RECORD: a PR draws
# several rounds of review, and round two overwriting round one destroys the very fact this
# exists to keep. One comment either way — thirty on a story is its own failure.
decisions = parsed.get("decisions") or []
if decisions:
    lines = []
    for entry in decisions:
        lines.append(f"- **{entry.get('decision', '').strip()}**")
        if entry.get("why"):
            lines.append(f"  - *Why:* {entry['why'].strip()}")
        if entry.get("supersedes"):
            lines.append(f"  - *Supersedes:* {entry['supersedes'].strip()}")
    attribution = f"**From {source}**{f' ({ROLES})' if ROLES else ''}{team.run_link()}"
    section = attribution + "\n" + "\n".join(lines)

    if team.append_to_comment(
        target,
        "<!-- claude-team:decisions -->",
        section,
        "### Decisions\n\nReached while the work was being done, so the issue above may still "
        "describe what they replaced. Newest last.",
    ):
        print(f"logged {len(decisions)} decision(s) from {source} on #{target}")
    else:
        team.warn(f"could not log decisions on #{target}")

# ── the handoff itself: one per task, or one per PR ─────────────────────────────────────
#
# Keyed on the TASK, not the story: a story has several authoring tasks and each has its own
# handoff, so a story-keyed marker would let the last one overwrite the rest. A PR follow-up has
# no task of its own, so it keys on the PR for the same reason.
key = ISSUE or f"pr-{PR}"
marker = f"<!-- claude-team:handoff:{key} -->"
body = (
    f"{marker}\n"
    f"### Handoff — {source}{f' ({ROLES})' if ROLES else ''}\n\n"
    "Machine-written, schema-enforced. `testingNotes` are for the Tester,\n"
    "`docsCandidates` for the Writer. An empty array is a real answer — it means the\n"
    "author considered it and found nothing, which is not the same as a missing key.\n\n"
    f"```json\n{HANDOFF}\n```\n"
)

if team.upsert_comment(target, marker, body + team.run_footer()):
    print(f"posted the handoff for {source} on story #{target}")
else:
    team.warn(f"could not post the handoff on #{target}")
