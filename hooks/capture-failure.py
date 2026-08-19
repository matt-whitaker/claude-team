#!/usr/bin/env python3
"""The other exit. A run that cannot land — its model step failed, or its landing conflicted —
gets its changes pushed to `failure/<task#>-<run#>` and a report on the issue. Recovery becomes
checkout, not transcript archaeology.

⚠️ EVERY AUTHOR RUN ENDS IN A SCRIPTED LANDING OR A SCRIPTED FAILURE CAPTURE. THERE IS NO THIRD
EXIT. The completion hook is gated off when a model step fails, because landing half-done work is
worse than landing nothing — so without this hook, a failed run's changes died with the runner.
Twice that was a finished feature, recovered only because the transcript happened to carry the
file contents.

⚠️ IT NEVER FAILS, AND NEVER MASKS. The run is already red for the real reason; a capture problem
becomes a warning, not a second failure for the reader to untangle. Exit code 0 on every path.

⚠️ THE COMMENT APPENDS. Each capture is a record — a re-triggered run that fails again pushes a
second failure branch, and replacing the first report would orphan the first branch. One comment,
sections stacking, same shape as the decisions log.

⚠️ `failure/*` DERIVES TO NOTHING BY CONSTRUCTION. `story_from_branch` reads a leading issue
number, and these names start with `failure/` — so no routing rule, kind derivation or landing
path can mistake a capture for a story branch. Checked, not assumed.
"""

from __future__ import annotations

import os
import subprocess

import team

GIT_IDENTITY = ["-c", "user.name=claude-team", "-c", "user.email=claude-team@users.noreply.github.com"]

ISSUE = os.environ.get("ISSUE", "")
RUN_ID = os.environ.get("GITHUB_RUN_ID", "0")
RUN_ATTEMPT = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
MODEL_FAILED = os.environ.get("MODEL_FAILED", "").lower() == "true"
UNLANDABLE = os.environ.get("UNLANDABLE", "").lower() == "true"

MARKER = "<!-- claude-team:failure-capture -->"

if not team.REPO:
    team.warn("REPO is not set — nothing captured.")
    raise SystemExit(0)

if not ISSUE:
    print("no issue — a PR follow-up's commits live on the PR's branch already. Nothing to capture.")
    raise SystemExit(0)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *GIT_IDENTITY, *args], capture_output=True, text=True, check=False)


# ⚠️ Same credential problem as the landing, and worse consequences: this hook IS the net. A
# capture that cannot push loses the run's work entirely — measured on run 31918402971.
if not team.authenticate_git():
    team.warn("no GH_TOKEN for git — the capture will use whatever credential the runner has.")

if git("status", "--porcelain").stdout.strip():
    git("add", "-A")
    git("commit", "-m", f"WIP capture from failed run {RUN_ID}")
    print("committed the uncommitted remainder for capture")

branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
base = git("merge-base", "HEAD", "origin/HEAD").stdout.strip() if branch else ""
ahead = git("rev-list", "--count", f"{base}..HEAD").stdout.strip() if base else "?"
if not branch or branch == "HEAD":
    team.warn("could not determine the current branch — nothing captured.")
    raise SystemExit(0)

head = git("rev-parse", "HEAD").stdout.strip()
if not head:
    team.warn("could not resolve HEAD — nothing captured.")
    raise SystemExit(0)

# ⚠️ A CAPTURE THAT PRESERVES NOTHING MUST NOT CLAIM TO. A run can fail before producing anything
# — a setup failure always does — and pushing then leaves a branch identical to the default branch
# plus a comment telling the reader their work is safe on it. Measured on #748: the comment named
# `failure/748-…` at the default branch's own HEAD, 0 commits ahead, and its recovery command
# produced a clean checkout of mainline. ⚠️ That is the most dangerous message this system can
# write, because it tells a reader not to look further (#1107, #1110).
#
# ⚠️ FAIL OPEN. If ahead-ness cannot be determined, PUSH ANYWAY. An empty branch is noise; a lost
# capture is the thing this hook exists to prevent, and that asymmetry is why the unconditional
# push was right until it started lying about what it had preserved.
if ahead == "0":
    print(
        "nothing to capture — this run produced no commits beyond the branch it started from. "
        "No failure branch was created, because there is nothing on it to recover."
    )
    team.append_to_comment(
        ISSUE, MARKER,
        f"⚠️ **This run did not land — {'its landing hit a merge conflict' if UNLANDABLE else 'its model step failed'}** "
        f"— and it produced **no changes**, so there is nothing to recover. No failure branch was "
        f"created.{team.run_link()}",
        "🪂 **Failure captures.** Runs that could not land, each preserved on a `failure/*` branch. "
        "Nothing here is merged anywhere; these are recovery points, appended newest last.",
    )
    raise SystemExit(0)

# run id + attempt, the same scheme as the transcript key — a re-attempt shares the run id
ref = f"failure/{ISSUE}-{RUN_ID}-{RUN_ATTEMPT}"
pushed = git("push", "origin", f"HEAD:refs/heads/{ref}")
if pushed.returncode != 0:
    team.warn(
        f"could not push the capture to `{ref}` — the work is still on the runner's `{branch}` "
        f"and dies with it. git said: {team.scrub((pushed.stderr or pushed.stdout).strip())}"
    )
    raise SystemExit(0)

why = "its landing hit a merge conflict" if UNLANDABLE else "its model step failed"
if MODEL_FAILED and UNLANDABLE:
    why = "its model step failed and its landing hit a merge conflict"

team.append_to_comment(
    ISSUE, MARKER,
    f"⚠️ **This run did not land — {why}.** Its changes are preserved on "
    f"[`{ref}`](https://github.com/{team.REPO}/tree/{ref}) at `{head[:7]}`.\n\n"
    f"Recover with `git fetch origin {ref} && git checkout {ref}`, or re-trigger the task — a "
    f"fresh run starts from the story branch and this capture stays put.{team.run_link()}",
    "🪂 **Failure captures.** Runs that could not land, each preserved on a `failure/*` branch. "
    "Nothing here is merged anywhere; these are recovery points, appended newest last.",
)
print(f"captured to {ref} at {head[:7]} ({why})")
