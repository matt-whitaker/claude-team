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
# ⚠️ `role=outcome` pairs for all four author steps, because `||` cannot pick between them here.
# A skipped step's outcome is the truthy string "skipped", so the `||` chain used for
# `structured_output` would always take the first one and report the wrong step's fate.
OUTCOMES = os.environ.get("OUTCOMES", "")

if not team.REPO:
    team.fail("REPO is required")


def _outcome(role: str) -> str:
    for pair in OUTCOMES.split():
        name, _, value = pair.partition("=")
        if name == role:
            return value
    return ""


def _note(key: str, value: str) -> None:
    """A step output for the caller — used to ungate transcript capture."""
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as fh:
            fh.write(f"{key}={value}\n")


# ⚠️ THREE CASES, AND THIS USED TO PRINT ONE SENTENCE THAT WAS FALSE IN THE WORST OF THEM.
# It said "no author ran, or its step failed" — and the case that actually halts a story is the
# third: an author RAN, its step SUCCEEDED, and it returned nothing usable. Both halves of that
# sentence are false there, so the one line a reader got sent them looking for a skipped job or a
# red step, neither of which existed (#32). Measured on a consumer at v1.1: the tester step ran
# 2m27s and completed, `HANDOFF` was empty, every `closed`-gated step skipped, and the task sat
# open until a human closed it fourteen hours later — at which point nothing could open the
# story's PR at all (#31).
if not HANDOFF:
    ran = [r for r in ROLES.split() if _outcome(r) not in ("", "skipped")]
    if not ran:
        print("No handoff to post — no author ran.")
        raise SystemExit(0)

    failed = [r for r in ran if _outcome(r) != "success"]
    if failed:
        print(
            "No handoff to post — "
            + ", ".join(f"the {r} step {_outcome(r)}" for r in failed)
            + ". The red step above is the signal; this is not a separate fault."
        )
        raise SystemExit(0)

    # ⚠️ THE ONE THAT HALTS A STORY, AND IT REPORTED SUCCESS FOR AS LONG AS IT EXISTED. No task
    # closes, every `closed`-gated step skips, and nothing anywhere says why — so this is an
    # error, not a line. ⚠️ Keep the evidence too: `evidence=true` ungates transcript capture in
    # the caller, because WHY the step produced nothing is unknowable from anything else the run
    # keeps, and this is exactly the run that needed it.
    _note("evidence", "true")
    team.fail(
        "The "
        + ", ".join(ran)
        + " step ran and SUCCEEDED but returned no handoff, so this task will not close and the "
        "story is halted. Nothing failed upstream — the model emitted no structured output, or "
        "emitted something the schema rejected. Re-trigger the task; if it recurs, the captured "
        "transcript is the only artifact that can say which."
    )

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
