#!/usr/bin/env python3
"""Completes an author's run: commits its changes, lands them on the story's branch, closes the
task. No PR is involved, and no author runs git for any of this.

⚠️ THE COMMIT IS SCRIPTED TOO, which removes the last load-bearing git operation any author owned.
The message rides the author's structured output (`commitMessage`); absent, a deterministic
fallback is written from the task title. An author that committed anyway is harmless — whatever is
uncommitted is committed, whatever is ahead is landed.

⚠️ A REJECTED PUSH RECONCILES BY MERGE: pull latest, commit the merge commit, push. Two tasks of
one story can run concurrently — the workflow's concurrency group is keyed on the issue and cannot
be keyed on the story, since the group is evaluated before the story is resolved — so competing
landings are expected, not exceptional. A merge that CONFLICTS is not resolved by script: the step
fails loudly with `unlandable=true`, the commits stay safe on the run's branch, and resolution is
an Implementor call. Never a force-push, never silence.

⚠️ `remaining` DECIDES WHETHER THE TASK CLOSES. It is the author's only structured way to say it
did not finish. A task closed while its work is half-done is exactly the failure that let a story
reach its Tester with no feature to test.
"""

from __future__ import annotations

import json
import os
import subprocess

import team

GIT_IDENTITY = ["-c", "user.name=claude-team", "-c", "user.email=claude-team@users.noreply.github.com"]


def emit(closed: bool, unlandable: bool = False) -> None:
    """Say what happened, so the board step and the failure-capture step can follow.

    ⚠️ FALSE IS A REAL ANSWER. A task that reported `remaining` is still open and still In
    Progress; a consumer that treated "the hook ran" as "the task finished" would march an
    unfinished task to Done. `unlandable` is the conflict signal the failure-capture step keys on.
    """
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as handle:
            handle.write(f"closed={'true' if closed else 'false'}\n")
            handle.write(f"unlandable={'true' if unlandable else 'false'}\n")


ISSUE = os.environ.get("ISSUE", "")
HANDOFF = os.environ.get("HANDOFF", "")

MARKER = "<!-- claude-team:task-landed -->"

if not team.REPO:
    team.fail("REPO is required")

if not ISSUE:
    print("no issue — a PR follow-up commits to the branch it was triggered on. Nothing to land.")
    emit(False)
    raise SystemExit(0)

named = team.branch_line(team.issue_body(ISSUE))
if not named:
    print(f"#{ISSUE} carries no Branch line — nothing to land onto.")
    emit(False)
    raise SystemExit(0)

# ⚠️ THE SAME STRUCTURAL TEST THE ROUTING RULES USE, so the two can never disagree about what a
# task is: a task's Branch line names its STORY's branch, so the number it starts with is not its
# own. When they are EQUAL the issue owns that branch — a story worked as-is. It lands exactly the
# same way, onto its own named ref (created by the push if absent), with two differences at the
# end: the issue is NEVER closed here (its PR merging closes it, GitHub-natively), and the PR is
# opened by the next step rather than at some later task's completion.
OWNS = team.story_from_branch(named) == str(ISSUE)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *GIT_IDENTITY, *args], capture_output=True, text=True, check=False)


branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
if not branch or branch == "HEAD":
    team.fail("could not determine the current branch, so nothing could be landed")

handoff = {}
if HANDOFF:
    try:
        handoff = json.loads(HANDOFF)
    except json.JSONDecodeError:
        team.warn("the author's handoff was not valid JSON — treating the task as unfinished")
        handoff = {"remaining": ["the author's report could not be read"]}

dirty = bool(git("status", "--porcelain").stdout.strip())
if dirty:
    message = (handoff.get("commitMessage") or "").strip()
    if not message:
        title = (team.issue(ISSUE, "title") or {}).get("title") or ""
        message = f"Task #{ISSUE}: {title}" if title else f"Work from task #{ISSUE}"
    git("add", "-A")
    committed = git("commit", "-m", message)
    if committed.returncode != 0:
        team.fail(f"could not commit the run's changes: {team.scrub((committed.stderr or committed.stdout).strip())}")
    print(f"committed the run's changes: {message.splitlines()[0]}")

# ⚠️ Authenticate before ANY network git. The host action strips the checkout credential and
# leaves its own expiring one; without this the fetch below reads as "the ref does not exist" and
# the push fails outright. See team.authenticate_git.
if not team.authenticate_git():
    team.warn("no GH_TOKEN for git — the landing will use whatever credential the runner has.")

# ⚠️ Fetch the target explicitly: a task's story branch was fetched by the action's own setup,
# but an as-is story's named ref may not exist anywhere yet — a failed fetch means the push will
# CREATE it, and everything on this branch is the landing.
ref_exists = git("fetch", "origin", named).returncode == 0

# ⚠️ "DID THE RUN PRODUCE ANYTHING" IS MEASURED AGAINST WHERE THE RUN STARTED, NOT AGAINST THE
# NAMED REF, AND CONFLATING THE TWO REPORTED A CONFLICT FOR A RUN THAT CHANGED NOTHING. A task's
# base IS its story branch, so for a task the two questions coincide and this changes nothing. An
# as-is story is different: its run is cut from the DEFAULT branch while its named ref may be days
# old, so `origin/<named>..HEAD` counts the default branch's own history and is non-zero however
# little the run did. Measured on #748 — a Writer correctly changed nothing, and the landing
# reported "could not land 1 commit(s)" and a merge conflict against a ref from four days earlier.
# ⚠️ THE NAMED REF IS THE BASE FOR EVERY CASE, because `branch-navigation.py` upserts it before
# any author runs and the host action is handed it as `base_branch`. The run therefore STARTS at
# this ref, so `origin/<named>..HEAD` is exactly what this run contributed — no default-branch
# arithmetic, and no as-is special case. Previously an as-is run was cut from the default branch
# while `<named>` might be days old, which is what made a no-op run look like it had work to land.
base = f"origin/{named}"

produced = git("rev-list", "--count", f"{base}..HEAD").stdout.strip() if ref_exists or OWNS else ""
if ref_exists and produced in ("", "0"):
    # ⚠️ NO COMMITS IS NOT THE SAME AS UNFINISHED, AND CONFLATING THEM HALTED THE CASCADE. Some
    # tasks are checks — "confirm whether any spec document encodes positioning in offline terms" —
    # and their correct outcome is that nothing changed. This path used to `emit(False)` for all of
    # them, so a task that had done exactly what it was asked stayed open, never reached Done, and
    # stopped the story. Measured on #1140: the run reported success and #1139's next task was
    # never dispatched.
    #
    # ⚠️ THE DISCRIMINATOR ALREADY EXISTS AND WAS SIMPLY NOT REACHED. `remaining` is the author's
    # own structured statement of whether it finished, `[]` meaning "I looked, there is nothing" —
    # and the closing logic below already keys on it. This path returned thirty lines too early.
    # ⚠️ AN ABSENT HANDOFF IS NOT AN EMPTY `remaining`, AND COLLAPSING THEM CLOSED A TASK WHOSE
    # AUTHOR NEVER RAN. The handoff contract already states it: entries mean the author found
    # something, [] means it looked and found nothing, and NO handoff at all means no author ran
    # or its run died before posting. A setup step failing (the playwright CDN hang) skips the
    # model step, the workflow's completion gate reads skipped as not-failed, and this hook then
    # saw a clean tree plus an empty HANDOFF env — and closed the task as "nothing to do" while
    # dispatching the next wave (#1159, measured). The schema FORCES a real author to emit
    # `remaining`, so absence is proof the author never spoke — only an explicit [] closes.
    nothing_remaining = bool(HANDOFF) and handoff.get("remaining") == []
    if HANDOFF and not handoff:
        nothing_remaining = False
    if not HANDOFF:
        print(f"no commits and no handoff — the author never reported. #{ISSUE} stays open; re-trigger it.")
        emit(False)
        raise SystemExit(0)
    if nothing_remaining and not OWNS:
        team.upsert_comment(
            ISSUE, MARKER,
            f"{MARKER}\n✅ **Nothing to do, and that is the finding.** This task produced no commits "
            f"and the author reported nothing remaining, so it is complete. Recorded here because "
            f"an empty result and a run that did nothing look identical otherwise."
            f"{team.run_link()}",
        )
        if team.gh("issue", "close", ISSUE, "--repo", team.REPO, "--reason", "completed") is None:
            team.warn(f"#{ISSUE} had nothing to do but could not be closed")
            emit(False)
            raise SystemExit(0)
        team.mark_complete(ISSUE)
        print(f"#{ISSUE} had nothing to do — closed; the story continues.")
        emit(True)
        raise SystemExit(0)

    # ⚠️ An as-is story is never closed here — its PR targets the default branch and GitHub closes
    # it natively on merge. And a task that DID report `remaining` is genuinely unfinished.
    if OWNS:
        print(f"nothing to land — #{ISSUE} is worked as-is and produced no commits.")
    else:
        print(f"nothing to land, and the author reported work remaining — #{ISSUE} stays open.")
    emit(False)
    raise SystemExit(0)

if ref_exists:
    ahead = git("rev-list", "--count", f"origin/{named}..HEAD").stdout.strip()
else:
    ahead = git("rev-list", "--count", "HEAD").stdout.strip() or "?"
    print(f"`{named}` does not exist yet — the landing creates it.")


def push() -> subprocess.CompletedProcess:
    return git("push", "origin", f"HEAD:refs/heads/{named}")


pushed = push()
if pushed.returncode != 0:
    # ⚠️ Reconcile by merge, once. Another run landed first; pull its work, commit the merge
    # commit, push. A conflict means two tasks touched the same lines — a script must not pick a
    # side, so it aborts, leaves everything on this branch, and fails with the signal the
    # failure-capture step reads.
    print(f"push refused — reconciling `{named}` by merge")
    git("fetch", "origin", named)
    merged = git("merge", "--no-edit", f"origin/{named}")
    if merged.returncode != 0:
        git("merge", "--abort")
        emit(False, unlandable=True)
        team.fail(
            f"could not land {ahead} commit(s) on `{named}` — the merge conflicts, and a script "
            f"must not resolve it. ⚠️ The commits exist ONLY on the runner's `{branch}`, which is "
            f"destroyed with this job: they survive only if the failure capture pushes them, and "
            f"its comment on this issue is the record of whether it did. Resolution is an "
            f"Implementor call. git said: {team.scrub((merged.stderr or merged.stdout).strip())}"
        )
    pushed = push()
    if pushed.returncode != 0:
        emit(False, unlandable=True)
        team.fail(
            f"could not land on `{named}` even after merging — another run landed again while "
            f"this one reconciled. The commits are safe on `{branch}`. git said: "
            f"{team.scrub((pushed.stderr or pushed.stdout).strip())}"
        )

print(f"landed {ahead} commit(s) from `{branch}` onto `{named}`")
out = os.environ.get("GITHUB_OUTPUT")
if out:
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(f"landed_ref={named}\n")

remaining = handoff.get("remaining") or []

link = team.run_link()
if remaining:
    items = "\n".join(f"- {item}" for item in remaining)
    team.upsert_comment(
        ISSUE, MARKER,
        f"{MARKER}\n⚠️ **Landed on `{named}`, but this task is NOT finished.** The author reported "
        f"work remaining, so the issue stays open:\n\n{items}\n\nRe-trigger it to continue.{link}",
    )
    print(f"#{ISSUE} left open — {len(remaining)} item(s) remaining")
    emit(False)
    raise SystemExit(0)

if OWNS:
    # ⚠️ An as-is story is NOT closed here. Its PR targets the default branch, so GitHub closes it
    # natively on merge — closing it now would mark the story done with nothing merged, which is
    # the exact confusion the task/story split exists to prevent.
    team.upsert_comment(
        ISSUE, MARKER,
        f"{MARKER}\n✅ **Landed on `{named}`.** {ahead} commit(s), no work reported remaining. This "
        f"story is worked as-is: its PR opens next and closes this issue when it merges.{link}",
    )
    print(f"#{ISSUE} is worked as-is — left open for its PR's merge")
    emit(False)
    raise SystemExit(0)

team.upsert_comment(
    ISSUE, MARKER,
    f"{MARKER}\n✅ **Landed on `{named}`.** {ahead} commit(s), no work reported remaining. This task "
    f"has no PR of its own by design — its work reaches the default branch through the story's "
    f"PR.{link}",
)

if team.gh("issue", "close", ISSUE, "--repo", team.REPO, "--reason", "completed") is None:
    team.warn(f"landed on `{named}` but could not close #{ISSUE}")
    emit(False)
else:
    team.mark_complete(ISSUE)
    print(f"closed #{ISSUE}")
    emit(True)
