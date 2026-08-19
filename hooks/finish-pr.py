#!/usr/bin/env python3
"""Post-hook for every role that opens a PR. Does the three things a prompt kept being asked
to remember:

  1. points the PR at its story's branch
  2. labels the PR with the role(s) that worked it
  3. makes sure the body carries `Closes #<issue>` — UNLESS the author reported the task
     unfinished, in which case it makes sure the body does NOT

(1) and (3) each silently lose work. A PR that targets the default branch takes its task out
of the story model — it ships to prod on merge and the story never gets a PR. A missing
closing keyword means close-merged-work finds nothing to close, so the issue never reaches
Done, with nothing to signal it either way.

ROLES is a space-separated list because the authoring roles are gated steps in ONE job and
this runs once at the end of it. A single role is a list of one; the PR should carry the
whole trail, not whichever ran last.
"""

import json
import os
import re
import subprocess

import team

ROLES = os.environ.get("ROLES") or team.fail("ROLES is required")
ISSUE = os.environ.get("ISSUE", "")
HANDOFF = os.environ.get("HANDOFF", "")

if not team.REPO:
    team.fail("REPO is required")

# ⚠️ A TASK NO LONGER HAS A PR AT ALL — `land-on-story.py` pushes its commits onto the story's
# branch and closes it. Everything below this point is about a PR, so for a task there is nothing
# here to do, and doing it would recreate the per-task PRs the model was changed to remove.
#
# ⚠️ THE STORY-WORKED-AS-IS PATH IS UNTOUCHED and must stay that way: that issue owns its own
# `Branch:` line, nothing sits between it and the default branch, and its PR is the whole point.
# The test is the existing structural one — a task's Branch line names a *different* issue's
# branch, so the number it starts with is not its own. Reusing it is what keeps this hook and the
# landing hook from ever disagreeing about what a task is.
if ISSUE:
    _named = team.branch_line(team.issue_body(ISSUE))
    if _named and team.story_from_branch(_named) != str(ISSUE):
        print(f"#{ISSUE} is a task — its work lands on `{_named}`; no PR to finish.")
        raise SystemExit(0)

branch = subprocess.run(
    ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=False
).stdout.strip()

pr = ""
if branch and branch != "HEAD":
    found = team.gh_json(
        "pr", "list", "--repo", team.REPO, "--head", branch, "--state", "open", "--json", "number"
    )
    if found:
        pr = str(found[0]["number"])

# the model may have moved off the branch it pushed; fall back to the issue
if not pr and ISSUE:
    listing = team.gh_json(
        "pr", "list", "--repo", team.REPO, "--state", "open", "--json", "number,body"
    ) or []
    closes = re.compile(rf"(?i)(clos|fix|resolv)[a-z]*\s+#{ISSUE}\b")
    match = next((p for p in listing if closes.search(p.get("body") or "")), None)
    if match:
        pr = str(match["number"])

if not pr:
    # ⚠️ "No PR" is not automatically "nothing happened". The host action creates its own
    # branch for an issue trigger and tells the model to stay on it, contradicting our
    # prompt — and when the model obeys it, a run's work lands somewhere nobody looks. It
    # happened on a 44-turn run that reported success (#530). Silence there cost days.
    #
    # So before accepting "nothing to finish", check whether this run actually produced
    # commits. If it did, say so loudly and leave the recovery command on the issue.
    stranded = ""
    default = (
        team.gh_json("repo", "view", team.REPO, "--json", "defaultBranchRef") or {}
    ).get("defaultBranchRef", {}).get("name") or ""
    if branch and branch != "HEAD":
        if default:
            ahead = subprocess.run(
                ["git", "rev-list", "--count", f"origin/{default}..HEAD"],
                capture_output=True, text=True, check=False,
            ).stdout.strip()
            if ahead.isdigit() and int(ahead) > 0:
                stranded = f"{ahead} commit(s) on `{branch}`"

    if not stranded:
        print("This run opened no PR — nothing to finish.")
        raise SystemExit(0)

    # ⚠️ OPEN THE PR, do not describe how to. This used to warn and leave a recovery
    # command, which is better than the silence it replaced but still left real work
    # sitting where nobody looks until someone read the comment.
    #
    # ⚠️ A PR, never a push. In the case that prompted this the branches had diverged, so
    # a push would have failed or needed force. A PR is non-destructive, reviewable, and
    # the shape the process wants anyway — work reaches a story branch through one.
    #
    # Base: the story branch the issue names, when it exists and is not what we are on;
    # otherwise the default branch. The host action generates its own branch name from
    # the issue title, which can never match a name the Architect already chose, so this
    # is the case prevention cannot reach.
    base = ""
    if ISSUE:
        named = team.branch_line(team.issue_body(ISSUE))
        if named and named != branch and team.gh(
            "api", f"repos/{team.REPO}/branches/{named}"
        ) is not None:
            base = named
    if not base:
        base = default

    title = (team.issue(ISSUE, "title").get("title") if ISSUE else "") or f"Work from {branch}"
    body = (
        f"Opened automatically: this run left {stranded} with no PR of its own.\n\n"
        f"The host action generates its own branch name, which cannot match a branch the "
        f"Architect already named — see #530. The work is sound; only its PR was missing.\n"
        + (f"\nCloses #{ISSUE}\n" if ISSUE else "")
    )

    if team.gh(
        "pr", "create", "--repo", team.REPO, "--base", base, "--head", branch,
        "--title", title, "--body", body,
    ) is None:
        team.warn(
            f"This run produced {stranded} and I could not open a PR for it. "
            f"Recover with: git push origin origin/{branch}:refs/heads/<the-branch-you-wanted>"
        )
        raise SystemExit(0)

    found = team.gh_json(
        "pr", "list", "--repo", team.REPO, "--head", branch, "--state", "open", "--json", "number"
    )
    if not found:
        team.warn(f"Opened a PR from {branch} but could not read it back to finish it.")
        raise SystemExit(0)
    pr = str(found[0]["number"])
    print(f"opened PR #{pr} from {branch} into {base} — it had {stranded} and none of its own")

# ⚠️ A TASK PR MUST TARGET ITS STORY'S BRANCH, and `gh pr create --base` is a model
# instruction like any other. #564 targeted the default branch — correctly, that time, because
# the story branch was missing — but the same slip with the branch present takes the task out
# of the story model: it ships straight to the deploy branch and the story never gets a PR at
# all, since open-story-pr only fires when a merged PR's base is a story branch.
#
# ⚠️ Retarget only when the named branch really exists and is not this PR's own head. A story
# triggered directly resolves its Branch line to the branch the PR is already FROM, and
# GitHub rejects a PR whose base is its head.
#
# ⚠️ UNLESS THE ISSUE *IS* THE STORY, which is the opposite case and wants the opposite base.
# A task's Branch line names its story's branch, so `story_from_branch(named) != ISSUE`. When
# they are EQUAL the executing issue owns that branch — the story is implementable as-is, its
# work is the whole story, and there is no parent for it to merge into.
#
# Retargeting one of those onto the story branch produces the mess this rule exists to stop:
# the work lands on a branch nobody has merged, `close-merged-work.py` closes the story anyway,
# and finishing it needs a second PR for an issue that is already closed. Measured on #751,
# whose story branch was empty and whose real work sat one branch further down (PR #865).
#
# So: that PR targets the DEFAULT branch, where its closing keyword fires natively and one merge
# finishes the story. The pre-created story branch is left unused — litter, not breakage.
if ISSUE:
    named = team.branch_line(team.issue_body(ISSUE))
    current = (
        team.gh_json("pr", "view", pr, "--repo", team.REPO, "--json", "baseRefName") or {}
    ).get("baseRefName") or ""
    owns_branch = bool(named) and team.story_from_branch(named) == str(ISSUE)

    if owns_branch:
        want = (
            team.gh_json("repo", "view", team.REPO, "--json", "defaultBranchRef") or {}
        ).get("defaultBranchRef", {}).get("name") or ""
        if want and want != current and want != branch:
            if team.gh("pr", "edit", pr, "--repo", team.REPO, "--base", want) is not None:
                print(f"PR #{pr} retargeted {current} -> {want} — #{ISSUE} is the story, not a task")
            else:
                team.warn(
                    f"PR #{pr} targets {current}; #{ISSUE} owns its branch so it belongs on {want}, "
                    "and I could not move it"
                )
        else:
            print(f"PR #{pr} targets {current} — #{ISSUE} is the story, nothing to retarget")
    elif (
        named
        and named != current
        and named != branch
        and team.gh("api", f"repos/{team.REPO}/branches/{named}") is not None
    ):
        if team.gh("pr", "edit", pr, "--repo", team.REPO, "--base", named) is not None:
            print(f"PR #{pr} retargeted {current} -> {named}")
        else:
            team.warn(f"PR #{pr} targets {current}, not the story branch {named}, and I could not move it")

for role in ROLES.split():
    if team.gh("pr", "edit", pr, "--repo", team.REPO, "--add-label", f"@claude/{role}") is not None:
        print(f"PR #{pr} -> @claude/{role}")
    else:
        team.warn(f"could not label PR #{pr} — does @claude/{role} exist in this repo?")

if not ISSUE:
    print("No triggering issue — nothing to close.")
    raise SystemExit(0)

# ⚠️ AN AUTHOR HAS TO BE ABLE TO SAY "NOT FINISHED", and for a long time it could not. The only
# gesture available was leaving the keyword out of the PR body, and this hook put it back —
# it asked whether the keyword was there, never why it was absent. #617 closed as COMPLETED with
# its wiring never written, and the Tester that ran next found no feature to test.
#
# ⚠️ THE SCHEMA WINS OVER THE PROSE, and that is the whole design. `remaining` is forced by
# `--json-schema`; a body is something a model may write anything into, including a closing
# keyword that contradicts its own report. So a non-empty `remaining` also STRIPS a keyword the
# model wrote, rather than warning about the contradiction and letting the task close anyway.
#
# ⚠️ ABSENT OR UNPARSABLE HANDOFF STILL CLOSES. That means the author's step failed or never ran,
# which is not the same as "incomplete" — three states, not two — and the net against a merely
# forgotten keyword has to stay in place for it.
remaining = []
if HANDOFF:
    try:
        parsed = json.loads(HANDOFF)
        if isinstance(parsed.get("remaining"), list):
            remaining = [str(item).strip() for item in parsed["remaining"] if str(item).strip()]
    except json.JSONDecodeError:
        team.warn("could not parse the handoff — treating this task as finished, as before.")

closes = re.compile(rf"(?i)\b(clos|fix|resolv)[a-z]*(\s+)#{ISSUE}\b")
body = (team.gh_json("pr", "view", pr, "--repo", team.REPO, "--json", "body") or {}).get("body") or ""

if remaining:
    listed = "\n".join(f"- {item}" for item in remaining)
    # a bare `#N` cross-references without the closing semantics, so the PR stays discoverable
    # from the task while `close-merged-work.py` finds nothing to close
    stripped = closes.sub(rf"refs\g<2>#{ISSUE}", body)
    note = (
        f"\n\n> [!WARNING]\n"
        f"> **This does not finish #{ISSUE}, and merging it will not close it.**\n"
        f"> The author reported the task incomplete. Still to do:\n"
        + "".join(f"> - {item}\n" for item in remaining)
    )
    if team.gh("pr", "edit", pr, "--repo", team.REPO, "--body", stripped + note) is None:
        team.warn(f"could not mark PR #{pr} as not finishing #{ISSUE} — it may close the task on merge")
    else:
        print(f"PR #{pr} -> withheld 'Closes #{ISSUE}': {len(remaining)} item(s) remaining")

    # ⚠️ ON THE TASK TOO. The PR body is where the merge decision happens; the task is where
    # someone looks afterwards and asks why it is still open. A PR comment is not durable for an
    # issue — the lesson #654 was filed for.
    #
    # Upserted, not appended, unlike the decisions log: this is a snapshot of what is left right
    # now, and an earlier run's list is superseded rather than part of a record.
    team.upsert_comment(
        ISSUE,
        f"<!-- claude-team:remaining:{ISSUE} -->",
        f"<!-- claude-team:remaining:{ISSUE} -->\n"
        f"### Left unfinished\n\n"
        f"PR #{pr} does not close this. Still to do:\n\n{listed}\n" + team.run_footer(),
    )
    raise SystemExit(0)

if closes.search(body):
    print(f"PR #{pr} already closes #{ISSUE}.")
    raise SystemExit(0)

team.gh("pr", "edit", pr, "--repo", team.REPO, "--body", f"{body}\n\nCloses #{ISSUE}\n")
print(f"PR #{pr} -> added 'Closes #{ISSUE}'")
