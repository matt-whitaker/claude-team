#!/usr/bin/env python3
"""Opens the STORY's PR when the LAST task completes — not before. The target experience is:
trigger the story, come back to a finished PR carrying the whole story's work.

⚠️ THE ALL-TASKS-CLOSED GATE LIVES HERE, IN THE HOOK, so every call site inherits it: the
authors job calls this after each landing, and the merge path still calls it as a net. A landing
that is not the last simply reports how many remain.

⚠️ AN UNREADABLE OR EMPTY TASK LIST DEGRADES TO OPEN-WHEN-AHEAD, WITH A WARNING. A rate-limited
minute must not permanently block the story's PR — and a story branch with no tasks at all is
off-model, worth a warning in its own right. Failing "open" here is deliberate: an early PR is a
nuisance, a story that can never get its PR is lost work.

BASE is the story branch. On the merge path it is the merged PR's base ref; merged into the
default branch it is a story PR itself, and there is nothing to open.
"""

import os

import team

BASE = os.environ.get("BASE", "")

if not team.REPO:
    team.fail("REPO is required")

repo = team.gh_json("repo", "view", team.REPO, "--json", "defaultBranchRef") or {}
default = (repo.get("defaultBranchRef") or {}).get("name") or ""

if not BASE or BASE == default:
    print(f"Merged into {BASE or '?'} — not a story branch, nothing to open.")
    raise SystemExit(0)

# A story branch is `<story#>-<summary>`. The number it starts with is the story — the same
# derivation delegate uses, so the two cannot disagree about which issue a branch belongs to.
story = team.story_from_branch(BASE)
if not story:
    team.warn(f"base {BASE} does not start with an issue number — cannot resolve its story.")
    raise SystemExit(0)

existing = team.gh_json(
    "pr", "list", "--repo", team.REPO, "--head", BASE, "--state", "open", "--json", "number"
)
if existing:
    print(f"PR #{existing[0]['number']} already open for {BASE}.")
    raise SystemExit(0)

tasks = team.sub_issues(story)
# ⚠️ NO TASKS IS THE AS-IS CASE, not an error: a story worked directly lands on its own ref and
# its PR opens the moment it is ahead. (An unreadable task list on a real task-story arrives here
# too and opens early — accepted, because an early PR is a nuisance and a story that can never get
# its PR is lost work.)
if not tasks:
    print(f"#{story} has no tasks — worked as-is; its PR opens as soon as the branch is ahead.")
else:
    remaining = [t_ for t_ in tasks if t_.get("state") != "closed"]
    if remaining:
        print(
            f"{len(remaining)} of {len(tasks)} task(s) still open — the story PR opens when the "
            "last one completes."
        )
        raise SystemExit(0)

compare = team.gh_json("api", f"repos/{team.REPO}/compare/{default}...{BASE}") or {}
if not compare.get("ahead_by"):
    print(f"{BASE} is not ahead of {default} — nothing to open a PR for.")
    raise SystemExit(0)

title = team.issue(story, "title").get("title") or f"Story #{story}"

if tasks:
    summary = ("**Every task has landed** — this PR carries the story's combined work to the "
               "default branch, and is its only review surface.")
else:
    summary = ("**Worked as-is** — this story was small enough for one author, and this PR is "
               "its whole delivery.")
lines = [
    f"Story PR for `{BASE}`.",
    "",
    summary,
    "",
    f"Closes #{story}",
]
if tasks:
    lines += ["", "### Tasks", ""]
    for task in tasks:
        mark = "x" if task.get("state") == "closed" else " "
        lines.append(f"- [{mark}] #{task['number']} — {task.get('title', '')}")
    # ⚠️ NO CLOSING KEYWORDS IN THIS LIST, and the reason changed even though the rule did not.
    # It used to be "each task is closed by its own PR merging into this branch" — false since a
    # task stopped having a PR at all. The rule survives because `work-completion.py` has ALREADY
    # closed these tasks by the time this list is written: repeating keywords here would re-close
    # finished ones on the story's merge, and close any that were abandoned rather than finished.
    # ⚠️ Kept explicit because the correct rule with a stale reason attached is exactly what gets
    # "simplified" away by someone who notices only that the reason is wrong.

if team.gh(
    "pr", "create", "--repo", team.REPO, "--base", default, "--head", BASE,
    "--title", title, "--body", "\n".join(lines) + "\n",
) is not None:
    print(f"opened the story PR for {BASE}")
else:
    # ⚠️ FAILS THE STEP, and that is the whole lesson of this hook's history. It warned instead,
    # for as long as it existed, while `pull-requests: read` made the create 403 every single
    # time — so it never once worked, the job stayed green, and the docs went on describing it as
    # the mechanism. A story branch then sat unmerged with nobody looking, and its work was lost
    # (#735/#815).
    #
    # ⚠️ Reaching this line means a PR genuinely should exist: every benign case — merged into the
    # default branch, an unresolvable story, a PR already open, a branch not ahead — returned
    # earlier. So there is no legitimate reason to be here and quiet.
    team.fail(f"could not open the story PR for {BASE} — open it by hand.")
