#!/usr/bin/env python3
"""One decision, made wherever branching matters: does the right branch exist for this issue —
and if not, should it. Authors never handle their own branching; this hook and the host action's
`base_branch` input do it between them.

THE UNIFIED RULE, applied identically at every call site:

  no Branch line          -> nothing to do (an epic and a spike have none by design)
  branch exists           -> leave it alone; make sure the story's Branch line carries its
                             compare link
  missing, TASK case      -> the line names the STORY's branch; create it at the default head
                             so the run's `base_branch` resolution cannot 404
  missing, STORY case     -> create only when the story HAS TASKS; a story worked as-is gets no
                             branch — its author cuts from the default branch and its PR goes
                             there directly

⚠️ THE HAS-TASKS QUESTION IS ANSWERABLE HERE NOW, AND THAT IS WHAT DISSOLVED THE OLD FRONT/BACK
SPLIT. The predecessor ran before `file-sub-issues.py`, where `sub_issues()` read 0 for every
story — including one the Architect had just decomposed — so story-branch creation had to be
deferred to a custodial back half that ran after parenting. The Architect's call site now sits
AFTER `file-sub-issues.py`, the count is real at every caller, and the back half is gone.

⚠️ POST ON THE ARCHITECT, NEVER PRE — this inverts the obvious implementation. `setupBranch`
checks whether the name it is about to generate already exists remotely and, if it does, throws
away our template and falls back to `claude/<entity>-<n>-<timestamp>`. Our template mints exactly
the name the Architect records, so pushing it up front would collide with the action's own
generation and strand the whole run on a `claude/...` branch nobody looks at.

⚠️ PRE ON THE AUTHORS, AND THAT HALF IS THE #744 NET. `delegate.py` routes straight to the
stamped role whenever a `Branch:` line is present, so an issue filed with both routing lines
already written never meets the Architect — and `setupBranch` resolves the base branch before
anything else, so a missing one is a 404 that kills the job in ~3 seconds, before the model is
called.

⚠️ NEVER TOUCHES AN EXISTING BRANCH. Absent is the only case handled. An existing branch may
carry an author's commits, and resetting it would inflict the exact loss this hook prevents.

⚠️ THE API, NOT A PUSH: a ref created at the default head is empty by construction, which is what
the story model wants — the first landing is its first commit.

⚠️ ONE RESIDUAL, ON THE AUTHORS PATH. `setupBranch` names the task's working branch
`{{entityNumber}}-{{description}}` and falls back to `claude/...` on collision. For a story that
cannot collide (story and task numbers differ); for a BUG the story and task are the same issue,
so a collision is possible when the Branch line equals the title's first five words kebab-cased.
It degrades into the stranded-commit case `finish-pr.py` reports; dodging it would mean
reimplementing the action's naming rule here, a worse trap than the collision.
"""

import os
import re

import team

ISSUE = os.environ.get("ISSUE", "")
KIND = os.environ.get("KIND", "")


def link_branch_line(branch: str, default: str) -> None:
    """Append a compare link to the Branch line, so opening the story's PR is one click.

    ⚠️ AFTER the closing backtick, never inside it. `team.branch_line` is anchored and captures
    only what sits between the backticks, so trailing text is invisible to it — a property to
    preserve deliberately, not to rely on by accident.

    Idempotent; one link serves the branch's whole life, because GitHub redirects a compare URL
    to the existing PR once one is open.
    """
    body = team.issue_body(ISSUE)
    if "/compare/" in body:
        print("the Branch line already carries its link")
        return

    url = f"https://github.com/{team.REPO}/compare/{default}...{branch}?expand=1"
    updated, count = re.subn(
        rf"^(\s*\*{{0,2}}branch:\s*`{re.escape(branch)}`\*{{0,2}})",
        lambda m: f"{m.group(1)} · [open its PR]({url})",
        body, count=1, flags=re.IGNORECASE | re.MULTILINE,
    )
    if not count:
        team.warn(f"could not find #{ISSUE}'s Branch line to link")
        return

    if team.gh("issue", "edit", str(ISSUE), "--repo", team.REPO, "--body", updated) is not None:
        print(f"linked the Branch line -> {url}")
    else:
        team.warn(f"could not write the PR link onto #{ISSUE}'s Branch line")


if not team.REPO:
    team.fail("REPO is required")

if not ISSUE:
    print("Not triggered on an issue — no branch to navigate.")
    raise SystemExit(0)

if KIND in ("epic", "spike"):
    print(f"#{ISSUE} is {'an epic' if KIND == 'epic' else 'a spike'} — it has no branch.")
    raise SystemExit(0)

named = team.branch_line(team.issue_body(ISSUE))
if not named:
    team.warn(
        f"#{ISSUE} carries no Branch line, so there is no story branch to create. Every role "
        "that follows reads that line to know where to commit; without it the story cannot be "
        "worked. Re-run the Architect on it."
    )
    raise SystemExit(0)

default = (
    team.gh_json("repo", "view", team.REPO, "--json", "defaultBranchRef") or {}
).get("defaultBranchRef", {}).get("name")
if not default:
    team.warn(f"could not read the default branch, so nothing could be done for {named}")
    raise SystemExit(0)

# Resolved BEFORE the exists check, so a re-run on an already-cut story still gets its link.
if team.gh("api", f"repos/{team.REPO}/branches/{named}") is not None:
    print(f"branch {named} already exists — leaving it alone")
    link_branch_line(named, default)
    raise SystemExit(0)

# ⚠️ A BRANCH EXISTS BECAUSE AN AUTHOR IS ABOUT TO WORK, NOT BECAUSE AN ISSUE WAS SHAPED. This
# hook is now called from the authors job alone — the Architect and the Researcher no longer call
# it. Shaping and answering produce nothing to commit, so a branch cut at those moments sits empty
# unless and until someone is dispatched to it. The authors job is also the only one that passes
# `base_branch` to the host action, so it is the only place a missing ref can 404.
#
# ⚠️ IT FOLLOWS THAT THE BRANCH APPEARS LATE, AND THAT IS INTENDED. A story shaped today and worked
# next week has no ref in between; its `Branch:` line is a name the first author run makes real.
# Nothing resolves that name before then.
#
# ⚠️ UPSERT, UNCONDITIONALLY. This used to return early for a story with no tasks — "worked
# as-is, so it needs no branch of its own" — and that single exception was the root of three
# failures. Its `Branch:` line named a ref that did not exist and the compare link beside it 404'd;
# `delegate.py` had to blank `story_branch` to stop the host action resolving it, which rule 1 (an
# explicit handle) did not do, so `@claude/writer` on such a story 404'd in 3.6s before the model
# was called (#746); and `work-completion.py` needed a "does the named ref exist yet" fork.
#
# ⚠️ It did not even save a branch. #746 produced two `failure/*` branches and no story branch —
# create-nothing made the debris unpredictable rather than absent. Nothing deletes branches here
# (that capability was removed on purpose), so avoiding creation was never balanced by cleanup.
#
# ⚠️ AND IT FIXES A CLASS OF ARITHMETIC BUG STRUCTURALLY. With the branch always present,
# `base_branch` is always set, so a run STARTS at the story branch and `origin/<named>..HEAD` is
# exactly what that run contributed. The stale-ref comparison that made a no-op run look like it
# had commits to land (#1110/#1111) cannot arise.
head = team.gh_json("api", f"repos/{team.REPO}/git/ref/heads/{default}") or {}
sha = (head.get("object") or {}).get("sha")
if not sha:
    team.warn(f"could not read {default}'s head, so {named} was not created")
    raise SystemExit(0)

if team.gh(
    "api", "--method", "POST", f"repos/{team.REPO}/git/refs",
    "-f", f"ref=refs/heads/{named}", "-f", f"sha={sha}",
) is None:
    team.warn(f"could not create branch {named} at {default}@{sha[:7]}")
    raise SystemExit(0)

print(f"created branch {named} at {default}@{sha[:7]} — empty, ready for its first landing")
link_branch_line(named, default)
