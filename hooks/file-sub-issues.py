#!/usr/bin/env python3
"""Post-hook for the Architect. Parents an epic's sub-issues to it and copies the epic's
milestone down.

Children are DISCOVERED, not declared. This used to read a machine-readable manifest the
model left in a comment; across nine epics it wrote one exactly once, so the hook silently
filed nothing.

⚠️ THE ANCHOR IS THE `Branch:` LINE, not prose. It replaced an `epic #N`/`story #N` reference
that read as reliable and was not: no prompt ever required it, so a run that omitted it filed
nothing and said nothing. A task's Branch line cannot be skipped — routing reads it, so a task
without one does not work at all — and its leading number is the story. The prose reference is
still honoured, because it is the only anchor an EPIC has: a story's Branch line names itself,
not its epic. See claims_parent.

A manifest is still honoured when one exists, unioned with what was discovered, so epics
decomposed under the old contract keep working.
"""

import json
import os
import re

import team

ISSUE = os.environ.get("ISSUE") or team.fail("ISSUE is required")

if not team.REPO:
    team.fail("REPO is required")

children: set[int] = set()

comments = team.gh_json("api", f"repos/{team.REPO}/issues/{ISSUE}/comments", "--paginate") or []
manifests = [c.get("body") or "" for c in comments if "owner-manifest" in (c.get("body") or "")]
if manifests:
    found = re.search(r"owner-manifest\s*(\{.*?\})\s*-->", manifests[-1], re.S)
    listed = []
    if found:
        try:
            listed = json.loads(found.group(1)).get("children") or []
        except json.JSONDecodeError:
            listed = []
    if listed:
        children.update(int(c) for c in listed)
        print(f"manifest on #{ISSUE} lists:", " ".join(str(c) for c in listed))
    else:
        team.warn(f"#{ISSUE} has an owner-manifest marker with no usable children — ignoring it.")

# The REST list endpoint, never the search API. Issue search is asynchronously indexed and
# these issues are seconds old when this hook runs, so a search would intermittently return
# nothing at all.
#
# Three markers, all required:
#   1. the author is a Bot — the Architect creates sub-issues through the action
#   2. the body claims this parent — see claims_parent below
#   3. a number above the parent's
#
# The body markers alone are not enough in a repo that documents its own conventions: a
# meta-issue quoting the convention verbatim satisfied every text rule and was adopted as a
# child of the issue it was describing. The author check is what makes this sound.
#
# The consequence is that a sub-issue the maintainer writes BY HAND is never auto-parented.
# That is the intended trade: this hook exists to clean up after the model.
#
# `.number > epic` is both a correctness filter and the pagination bound — a child is always
# created after its epic, so it always has a higher number.
listing = team.gh_json(
    "api", "--paginate",
    f"repos/{team.REPO}/issues?state=all&sort=created&direction=desc&per_page=100",
) or []
# the trailing (non-digit|end) stops `epic #412` from matching `epic #4123`
refers = re.compile(rf"(?i)(epic|story) +#{ISSUE}([^0-9]|$)")


def sequenced(parent: str) -> set[int]:
    """Issue numbers the parent's own `Sequencing` section names.

    ⚠️ THIS IS THE ONLY DETERMINISTIC ANCHOR AN EPIC HAS, and its absence is what left epic #1112
    with six orphaned issues and a hook reporting success. A story's Branch line names *itself*, so
    it can never point at its epic; the prose `epic #N` reference the hook fell back on is a marker
    **no prompt requires** — a risk this file's own docstring names and then depended on anyway.

    ⚠️ The section is not a new marker. `Sequencing` is the Architect's stated deliverable and
    `dispatch-next.py` already reads it, so this derives parentage from something the model must
    produce for another reason — the rule this package applies everywhere else.

    ⚠️ SCOPED TO THE SECTION, never the whole body. An epic body cites prior art, superseded issues
    and out-of-scope work; adopting every `#N` in it would parent unrelated issues irreversibly.
    """
    body = team.issue_body(parent)
    match = re.search(r"(?im)^(?:#{2,4}\s*sequencing\b|\*\*sequencing[.:]?\*\*)", body)
    if not match:
        return set()
    found: set[int] = set()
    for line in body[match.end():].splitlines():
        if re.match(r"^#{1,6}\s", line):
            break
        found.update(int(n) for n in re.findall(r"#(\d+)", line))
    return {n for n in found if n > int(parent)}


def claims_parent(body: str) -> bool:
    """Two anchors, unioned. The Branch line is the reliable one.

    ⚠️ THE PROSE REFERENCE IS NOT REQUIRED OF THE ARCHITECT ANYWHERE. Anchoring on it alone is
    the same mistake one level up from the manifest this hook already abandoned: a model-written
    marker that no prompt demands. Story #515's four tasks each carried both stamped lines and
    were all bot-authored, and every filter passed except this one — so nothing was filed,
    sub_issues came back empty, and log-to-story reported "no tasks" with nothing to signal it.

    The Branch line cannot be skipped: routing itself reads it, so a task without one does not
    work at all. Its leading number is the story.

    ⚠️ It resolves STORY -> TASK ONLY. A story's own Branch line names *itself*, not its epic,
    so an epic has nothing but the prose to go on — which is why both anchors stay. That
    asymmetry also means this can never adopt a story as its own child: the `number > parent`
    bound already excludes the parent itself.
    """
    return team.story_from_branch(team.branch_line(body)) == str(ISSUE) or bool(refers.search(body))


def discover(parent: str) -> set[int]:
    """Bot-authored issues, numbered above the parent, whose Branch line resolves to it."""
    branch_of = re.compile(rf"(?i)(epic|story) +#{parent}([^0-9]|$)")
    def claims(body: str) -> bool:
        return team.story_from_branch(team.branch_line(body)) == str(parent) or bool(branch_of.search(body))
    return {
        i["number"] for i in listing
        if not i.get("pull_request")
        and i.get("number", 0) > int(parent)
        and (i.get("user") or {}).get("type") == "Bot"
        and claims(i.get("body") or "")
    }


discovered = discover(ISSUE) | sequenced(ISSUE)
if discovered:
    print(f"discovered for #{ISSUE}:", " ".join(str(d) for d in sorted(discovered)))
else:
    print(f"nothing claims #{ISSUE} by Branch line, prose or Sequencing section")
children.update(discovered)

if not children:
    print(f"Nothing to file for #{ISSUE}.")
    raise SystemExit(0)

milestone = (team.issue(ISSUE, "milestone").get("milestone") or {}).get("title") or ""
existing = {i["number"] for i in team.sub_issues(ISSUE)}

for child in sorted(children):
    if child in existing:
        print(f"#{child} already a sub-issue of #{ISSUE}")
    else:
        # this API wants the child's integer REST id, not its issue number
        data = team.gh_json("api", f"repos/{team.REPO}/issues/{child}")
        # ⚠️ REJECT PULL REQUESTS HERE, WHERE BOTH ANCHORS PASS THROUGH. `discover()` filters
        # `pull_request` out of the issue listing; `sequenced()` reads raw `#N` references from a
        # Sequencing section and had no equivalent, so a story PR named there was offered up as a
        # child. Measured on #1112: `discovered for #1112: 1114 1123 1124`, and #1123 is a PR — it
        # escaped only because the API refused it. Guarding at the parenting step covers every
        # anchor, present and future, rather than patching one of them.
        if (data or {}).get("pull_request"):
            print(f"#{child} is a pull request, not an issue — not parented.")
            continue
        cid = (data or {}).get("id")
        if cid and team.gh(
            "api", "--method", "POST", f"repos/{team.REPO}/issues/{ISSUE}/sub_issues",
            "-F", f"sub_issue_id={cid}",
        ) is not None:
            print(f"#{child} -> sub-issue of #{ISSUE}")
        else:
            team.warn(f"could not parent #{child} to #{ISSUE}")

    if milestone:
        if team.gh("issue", "edit", str(child), "--repo", team.REPO, "--milestone", milestone) is not None:
            print(f"#{child} -> milestone {milestone}")
        else:
            team.warn(f"could not set milestone '{milestone}' on #{child}")


# ⚠️ ONE LEVEL DOWN, BECAUSE AN ARCHITECT DECOMPOSING AN EPIC CREATES TWO GENERATIONS IN ONE RUN.
# This hook only ever ran for the issue that triggered it, so when the trigger was an epic the
# story→task pass never happened at all — the tasks' Branch lines resolved perfectly and nothing
# ever asked them. Measured on epic #1112: six issues created, zero parented, the step green.
#
# ⚠️ Exactly one level. A task has no children, so recursing further would only re-scan the same
# listing to no purpose — and unbounded recursion over a parent-derived rule is how a cycle gets
# built out of a convention.
for parent in sorted(children):
    below = discover(str(parent)) - {parent} - children
    if not below:
        continue
    have = {i["number"] for i in team.sub_issues(parent)}
    for grandchild in sorted(below):
        if grandchild in have:
            print(f"#{grandchild} already a sub-issue of #{parent}")
            continue
        data = team.gh_json("api", f"repos/{team.REPO}/issues/{grandchild}")
        cid = (data or {}).get("id")
        if cid and team.gh(
            "api", "--method", "POST", f"repos/{team.REPO}/issues/{parent}/sub_issues",
            "-F", f"sub_issue_id={cid}",
        ) is not None:
            print(f"#{grandchild} -> sub-issue of #{parent}")
        else:
            team.warn(f"could not parent #{grandchild} to #{parent}")
