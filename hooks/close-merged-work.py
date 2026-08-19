#!/usr/bin/env python3
"""Runs on every merged PR. Closes the issues it finished and files them on the board.

TWO BEHAVIOURS, NOT ONE — this said they were the same and was half wrong.

  linking       a closing keyword in the body links the issue at ANY base. Measured on
                real PRs into story branches: #536 -> [521], #542 -> [522], #443 -> [441].
                closingIssuesReferences IS populated, so the primary path below finds it.
  auto-closing  GitHub only CLOSES on merge when the PR targets the DEFAULT branch. A
                task PR targets its story's branch, so nothing closes it on its own —
                which is why this hook exists.

The body parse below is a net for a PR whose keyword GitHub did not link, not the
mechanism. It is currently unreachable here; kept because a missing close is silent and
costs an issue that never reaches Done.

NO SUB-ISSUE EXPANSION. This used to close a closed issue's open children, because a story's
tasks had no PRs of their own and the story's merge was the only thing that could close them.
Every task now closes via its own PR merging into the story branch, so a task still open when
its story merges is a real signal — abandoned, or its PR never landed — and swallowing it
would hide exactly the case worth seeing.
"""

import os
import re

import team

PR = os.environ.get("PR") or team.fail("PR is required")
OWNER = os.environ.get("PROJECT_OWNER", "")
PROJECT = os.environ.get("PROJECT_NUMBER", "")

if not team.REPO:
    team.fail("REPO is required")

linked = team.gh_json("pr", "view", PR, "--repo", team.REPO, "--json", "closingIssuesReferences")
issues = [str(i["number"]) for i in (linked or {}).get("closingIssuesReferences", [])]

if not issues:
    body = (team.gh_json("pr", "view", PR, "--repo", team.REPO, "--json", "body") or {}).get("body") or ""
    issues = sorted(
        {m for m in re.findall(r"(?i)(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", body)},
        key=int,
    )
    if issues:
        print("No linked issues (non-default base); parsed from the body:", " ".join(issues))

if not issues:
    print(f"PR #{PR} closes no issue — nothing to do.")
    raise SystemExit(0)

for issue in issues:
    if team.issue_state(issue) == "OPEN":
        team.gh("issue", "close", issue, "--repo", team.REPO, "--comment", f"Completed by #{PR}.")
        print(f"Issue #{issue} -> closed")
    # ⚠️ EVERY issue on the merge path gets the marker swap, not only the ones this hook closed.
    # A story's own issue is closed NATIVELY by GitHub when its PR merges — no hook touches it —
    # so without this, every completed story kept `@claude` forever and read as in-flight (#1108).
    team.mark_complete(issue)

token = os.environ.get("PROJECTS_TOKEN", "")
if not token:
    team.warn(
        "PROJECTS_TOKEN is not set — issues closed, but not moved on the board. Add a classic "
        "PAT with the 'project' AND 'read:org' scopes (fine-grained tokens cannot reach "
        "user-owned Projects v2)."
    )
    raise SystemExit(0)

os.environ["GH_TOKEN"] = token

# Preflight, so a token problem warns instead of failing a merged PR. `gh project` needs
# read:org on top of project, even for a user-owned project, and its raw error never says
# which secret is at fault.
project = team.gh_json("project", "view", PROJECT, "--owner", OWNER, "--format", "json")
if not project:
    team.warn(
        f"PROJECTS_TOKEN cannot reach project {PROJECT} — issues were closed, but the board "
        "was not updated. `gh project` requires the 'read:org' scope in addition to 'project'."
    )
    raise SystemExit(0)

fields = team.gh_json("project", "field-list", PROJECT, "--owner", OWNER, "--format", "json") or {}
status_field = next((f for f in fields.get("fields", []) if f.get("name") == "Status"), None)
done = next((o for o in (status_field or {}).get("options", []) if o.get("name") == "Done"), None)
if not done:
    team.warn(f"Project {PROJECT} has no Status option named 'Done' — skipping the board update.")
    raise SystemExit(0)

listing = team.gh_json(
    "project", "item-list", PROJECT, "--owner", OWNER, "--format", "json", "--limit", "500"
) or {}
for issue in issues:
    item = next(
        (
            i for i in listing.get("items", [])
            if (i.get("content") or {}).get("type") == "Issue"
            and (i.get("content") or {}).get("number") == int(issue)
        ),
        None,
    )
    if not item:
        team.warn(f"Issue #{issue} is not on project {PROJECT} — skipping.")
        continue
    team.gh(
        "project", "item-edit", "--id", item["id"], "--project-id", project["id"],
        "--field-id", status_field["id"], "--single-select-option-id", done["id"],
    )
    print(f"Issue #{issue} -> Done")
