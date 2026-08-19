#!/usr/bin/env python3
"""Applies the root role's process repairs, records every one, and escalates a repeat.

⚠️ THE MODEL PROPOSES, THIS DISPOSES, and that split is what makes "never touches content"
checkable rather than promised. The role holds no mutating verb at all — its whole repertoire is
the enum below, and a repair it cannot name here is one it cannot make. So "no code, no spec, no
rewritten issue body" is enforced by what exists, not by a paragraph asking nicely.

⚠️ FIX AND REPORT, NEVER FIX QUIETLY. Every repair appends to one log comment on its target. The
value of this system has come from breakage being *visible*: #744's 404 is what produced #777, and
a custodian that had silently created the branch would have left a working run and a rule still
wrong, with nobody knowing to fix it.

⚠️ WHICH IS WHY A REPEAT ESCALATES. Reaching for the same repair on the same target twice means the
cause was never fixed and this is now papering over it — so the second attempt files an issue
instead of repairing, and says what it would have done. A custodian quietly repairing the same
thing weekly has become a suppressor of exactly the signal that would have fixed it properly.

⚠️ THE REPEAT CHECK READS THE LOG, not a memory of the last run. State on the issue is the only
thing that survives a run, and deriving from it is the rule this package keeps relearning.

⚠️ CREATING A MISSING BRANCH IS DELIBERATELY *NOT* IN THE REPERTOIRE, though it is the case that
motivated the role. Writing a ref needs `contents: write`, and the host action's base allowlist
unions in `Bash(git rm:*)` plus `git-push.sh` — which no role can remove. With `contents: read`
those are inert; with `contents: write` a run could delete files and push them, and the whole claim
that this role cannot touch content would rest on it holding no `Write` tool rather than on the
token. The branch case is already prevented upstream anyway, so the trade is a bad one. It goes in
`unrepairable`, where a human acts on it.
"""

from __future__ import annotations

import json
import os

import team

REPAIRS = os.environ.get("REPAIRS", "")
OWNER = os.environ.get("PROJECT_OWNER", "")
PROJECT = os.environ.get("PROJECT_NUMBER", "")
ISSUE = os.environ.get("ISSUE", "")
PR = os.environ.get("PR", "")

TARGET = ISSUE or PR

MARKER = "<!-- claude-team:custodian-log -->"
HEADER = (
    "🔧 **Custodian log.** What a run put right, and what it found and deliberately did not. "
    "Nothing here changed any content."
)
CLASSIFICATION = {"epic", "spike", "bug", "task", "story"}

if not team.REPO:
    team.fail("REPO is required")

if not REPAIRS.strip():
    print("no repair report from the run — nothing to apply.")
    raise SystemExit(0)

try:
    report = json.loads(REPAIRS)
except json.JSONDecodeError:
    team.warn("the repair report was not valid JSON — nothing applied.")
    raise SystemExit(0)

repairs = report.get("repairs") or []
unrepairable = report.get("unrepairable") or []


def already_repaired(target: str, kind: str) -> bool:
    """True when this exact repair is already recorded on the target.

    ⚠️ Matches on kind AND target, not on the prose. Two runs describing the same breakage in
    different words are still the same repair, and the whole point of escalation is to catch the
    second one.
    """
    comments = team.gh_json("api", f"repos/{team.REPO}/issues/{target}/comments", "--paginate")
    if not isinstance(comments, list):
        return False
    return any(
        MARKER in (c.get("body") or "") and f"`{kind}`" in (c.get("body") or "")
        for c in comments
    )


def apply(repair: dict) -> str | None:
    """Perform one repair. Returns a description of what changed, or None if nothing did."""
    kind = repair.get("kind")
    target = repair.get("target") or ""

    if not target.isdigit():
        team.warn(f"repair {kind} has a non-numeric target {target!r} — skipped.")
        return None

    if kind == "board-item":
        if not (OWNER and PROJECT):
            team.warn("no project configured — cannot place a board item.")
            return None
        url = f"https://github.com/{team.REPO}/issues/{target}"
        done = team.gh("project", "item-add", PROJECT, "--owner", OWNER, "--url", url)
        return f"added #{target} to project {PROJECT}" if done is not None else None

    if kind == "sub-issue-link":
        parent = repair.get("parent") or ""
        if not parent.isdigit():
            team.warn(f"sub-issue-link for #{target} has no numeric parent — skipped.")
            return None
        child = team.gh_json("api", f"repos/{team.REPO}/issues/{target}")
        if not isinstance(child, dict) or "id" not in child:
            return None
        done = team.gh(
            "api", "--method", "POST", f"repos/{team.REPO}/issues/{parent}/sub_issues",
            "-F", f"sub_issue_id={child['id']}",
        )
        return f"parented #{target} under #{parent}" if done is not None else None

    if kind == "classification-label":
        label = (repair.get("label") or "").lower()
        # ⚠️ The enum in the schema is not the guard — this is. A schema constrains a well-behaved
        # model; this constrains the output, and a routing label applied by accident would start
        # work nobody asked for.
        if label not in CLASSIFICATION:
            team.warn(f"refusing to apply {label!r} — only {sorted(CLASSIFICATION)} are allowed here.")
            return None
        done = team.gh("issue", "edit", target, "--repo", team.REPO, "--add-label", label)
        return f"labelled #{target} `{label}`" if done is not None else None

    return None


def escalate(repair: dict) -> None:
    """File an issue rather than repairing the same thing twice."""
    kind, target = repair.get("kind"), repair.get("target")
    team.gh(
        "issue", "create", "--repo", team.REPO,
        "--title", f"Recurring process repair: {kind} on #{target}",
        "--body",
        f"The custodian has now reached for a `{kind}` repair on #{target} more than once, so the "
        "cause was never fixed and repairing it again would just hide it.\n\n"
        f"**What is wrong:** {repair.get('wrong')}\n\n"
        f"**Why it happens:** {repair.get('why')}\n\n"
        f"⚠️ **This issue exists because the repair was withheld.** #{target} is still in the "
        "broken state — fix the cause, then put the instance right by hand." + team.run_footer(),
    )


applied, withheld = [], []

for repair in repairs:
    kind, target = repair.get("kind"), repair.get("target") or ""
    if kind == "report" or not target.isdigit():
        continue

    if already_repaired(target, kind):
        escalate(repair)
        withheld.append(f"`{kind}` on #{target} — already repaired once; filed an issue instead")
        continue

    changed = apply(repair)
    if changed:
        team.append_to_comment(
            target, MARKER,
            f"**`{kind}`** — {changed}.\n\n_What was wrong:_ {repair.get('wrong')}\n\n"
            f"_Why:_ {repair.get('why')}{team.run_link()}",
            HEADER,
        )
        applied.append(f"{kind} on #{target}: {changed}")


def report_unrepairable() -> None:
    """Put what the run would NOT fix where a human reads it, not only in the job log.

    ⚠️ THIS WAS A `print` TO THE ACTIONS LOG, AND THAT MADE IT THE FIFTH DEAD CHANNEL HERE — after
    `DEFAULTED`, the author handoff appended in a job its readers never run in, `decisions` on the
    PR path, and `docsCandidates`. Every one had the same shape: a required output with nothing
    reading it, shipped and believed to work.

    ⚠️ IT IS THE HALF THAT CARRIES THE WEIGHT, which is what made losing it expensive. `repairs`
    are the things already put right; `unrepairable` is the finding a human must act on — usually
    naming the role that owns it. A measured instance: a run identified a stale task title and
    said which role should rename it. That sentence reached a job log and nobody else, so from the
    outside the custodian had said "not my job" and offered nothing.

    ⚠️ SAME MARKER AS THE REPAIRS, deliberately: everything the custodian has done to an issue
    reads as one history. The section prefix is what distinguishes them, so a reader can never
    mistake "I did not fix this" for "I fixed this".

    ⚠️ APPENDS RATHER THAN UPSERTS, matching `repairs`. A finding is a record, not a derived
    status — and a *repeated* finding is itself the signal that the cause is still there, which an
    upsert would erase.
    """
    if not unrepairable:
        return

    lines = [
        f"⚠️ **Not repaired** — {item.get('what')}\n\n_What would fix it:_ {item.get('wouldFix')}"
        for item in unrepairable
    ]
    for item in unrepairable:
        print(f"reported only — {item.get('what')} (would fix: {item.get('wouldFix')})")

    if not TARGET:
        team.warn(
            f"{len(unrepairable)} unrepairable finding(s) had no issue or PR to report on — "
            "ISSUE and PR were both empty, so they reached the job log only."
        )
        return

    if not team.append_to_comment(TARGET, MARKER, "\n\n".join(lines) + team.run_link(), HEADER):
        team.warn(f"could not report {len(unrepairable)} unrepairable finding(s) on #{TARGET}")


for line in applied:
    print(f"repaired — {line}")
for line in withheld:
    print(f"withheld — {line}")

report_unrepairable()

if not (applied or withheld or unrepairable):
    print("no repairs applied.")
