#!/usr/bin/env python3
"""One custodial responsibility, three modes: if a label has yet to be applied, apply it; if the
task or story status is not updated, update it. Consolidates what were four hooks — the role
stamp, the kind label, the board status, and the custodial kind sweep — because they are one
intent with one failure mode: bookkeeping a model could forget, made deterministic.

  MODE=stamp   stamp `@claude/<role>` on the triggering issue or PR (ROLE, NUMBER)
  MODE=kind    apply the classification label an issue's kind calls for (ISSUE)
  MODE=status  put an issue on the project board with the Status it should have (ISSUE, STATUS)

⚠️ ROUTING LABELS ARE STAMPED, CLASSIFICATION LABELS ARE DERIVED, AND NEITHER IS EVER REMOVED.
`@claude/<role>` is a record of what has run. `epic`/`spike`/`bug`/`task`/`story` say what an
issue *is*, asked of `team.kind()` — never matched from the title here, so precedence lives in
one place. An issue already carrying ANY kind label is left alone: a maintainer who relabelled
something by hand meant it.

⚠️ `kind` REFUSES TO WRITE WHEN IT CANNOT READ. Every issue has a title, so a missing one means
the READ failed — `kind()` would default to `story`, and writing on that would label an epic
`story` for the duration of a rate limit.

⚠️ INCLUDE_SUB_ISSUES extends `kind` and `status` to the issue's children. The tasks are why:
a trigger-only pass labels the story and never the tasks the Architect just created, and tasks
are the most numerous kind. The children are only discoverable after `file-sub-issues.py`, so
sub-issue passes run after it.

⚠️ `status` IS ONE OF THE TWO PLACES PROJECTS_TOKEN MAY APPEAR, and only in step env on a
scripted step — a model step in the same job cannot read it. Adding to the board is part of the
job: "set the status" and "be on the board" are one intent, and splitting them is what once left
every Architect-created issue off the board.

⚠️ ONLY_IF_UNSET is for the placing caller: an Architect re-run on a story already In Progress
must not knock live work back to Todo. The authors' caller omits it — moving to In Progress
*should* override whatever was there.
"""

from __future__ import annotations

import os

import team

MODE = os.environ.get("MODE", "")
ISSUE = os.environ.get("ISSUE", "")
NUMBER = os.environ.get("NUMBER", "")
ROLE = os.environ.get("ROLE", "")
STATUS = os.environ.get("STATUS", "")
ONLY_IF_UNSET = os.environ.get("ONLY_IF_UNSET", "").lower() == "true"
INCLUDE_SUB_ISSUES = os.environ.get("INCLUDE_SUB_ISSUES", "").lower() == "true"
OWNER = os.environ.get("PROJECT_OWNER", "")
PROJECT = os.environ.get("PROJECT_NUMBER", "")

if not team.REPO:
    team.fail("REPO is required")


def add_label(number: str | int, label: str) -> bool:
    # the /labels endpoint serves pull requests too; a repeat add is a no-op
    return team.gh(
        "api", f"repos/{team.REPO}/issues/{number}/labels", "-f", f"labels[]={label}"
    ) is not None


def stamp() -> None:
    if not ROLE:
        team.fail("MODE=stamp requires ROLE")
    if not NUMBER:
        print("No issue or PR number on this event — nothing to stamp.")
        return
    if add_label(NUMBER, f"@claude/{ROLE}"):
        print(f"#{NUMBER} -> @claude/{ROLE}")
    else:
        team.warn(f"could not stamp @claude/{ROLE} on #{NUMBER} — does the label exist in this repo?")


def kind_one(number: str | int) -> None:
    data = team.issue(number, "title", "labels")
    if not data.get("title"):
        team.warn(f"could not read #{number} — leaving its labels alone rather than guessing.")
        return
    names = {(l.get("name") or "").lower() for l in data.get("labels", [])}
    if names & set(team.KIND_LABELS.values()):
        print(f"#{number} already carries a kind label.")
        return
    wanted = team.KIND_LABELS[team.kind(number, data)]
    if add_label(number, wanted):
        print(f"#{number} -> {wanted}")
    else:
        team.warn(f"could not label #{number} — does the '{wanted}' label exist in this repo?")


def kind() -> None:
    if not ISSUE:
        print("Not triggered on an issue — nothing to label.")
        return
    kind_one(ISSUE)
    if INCLUDE_SUB_ISSUES:
        for child in team.sub_issues(ISSUE):
            kind_one(child["number"])


def status() -> None:
    if not STATUS:
        team.fail("MODE=status requires STATUS")
    if not ISSUE:
        print("Not triggered on an issue — nothing to move.")
        return
    token = os.environ.get("PROJECTS_TOKEN", "")
    if not token:
        team.warn(f"PROJECTS_TOKEN is not set — cannot set #{ISSUE} to {STATUS}.")
        return
    os.environ["GH_TOKEN"] = token

    # `--owner "@me"`, never the literal login: gh otherwise probes user-vs-org, which needs
    # read:org and fails with a bare "unknown owner type".
    project = team.gh_json("project", "view", PROJECT, "--owner", OWNER, "--format", "json")
    if not project:
        team.warn(
            f"PROJECTS_TOKEN cannot reach project {PROJECT} — needs 'read:org' as well as 'project'."
        )
        return

    fields = team.gh_json("project", "field-list", PROJECT, "--owner", OWNER, "--format", "json") or {}
    status_field = next((f for f in fields.get("fields", []) if f.get("name") == "Status"), None)
    option = next(
        (o for o in (status_field or {}).get("options", []) if o.get("name") == STATUS), None
    )
    if not option:
        team.warn(f"Project {PROJECT} has no Status option named '{STATUS}' — skipping.")
        return

    listing = team.gh_json(
        "project", "item-list", PROJECT, "--owner", OWNER, "--format", "json", "--limit", "500"
    ) or {}
    on_board = {
        (i.get("content") or {}).get("number"): i
        for i in listing.get("items", [])
        if (i.get("content") or {}).get("type") == "Issue"
    }

    def place(number: str | int) -> None:
        if team.issue_state(number) != "OPEN":
            print(f"#{number} is closed — leaving its board status alone.")
            return
        item = on_board.get(int(number))
        if not item:
            added = team.gh_json(
                "project", "item-add", PROJECT, "--owner", OWNER,
                "--url", f"https://github.com/{team.REPO}/issues/{number}", "--format", "json",
            )
            if not (added or {}).get("id"):
                team.warn(f"could not add #{number} to project {PROJECT}")
                return
            print(f"#{number} -> added to project {PROJECT}")
            item = {"id": added["id"], "status": None}

        current = item.get("status")
        if current == STATUS:
            print(f"#{number} is already {STATUS}.")
            return
        if ONLY_IF_UNSET and current:
            print(f"#{number} is already {current} — leaving it.")
            return

        if team.gh(
            "project", "item-edit", "--id", item["id"], "--project-id", project["id"],
            "--field-id", status_field["id"], "--single-select-option-id", option["id"],
        ) is None:
            team.warn(f"could not set #{number} to {STATUS}")
            return
        print(f"#{number} -> {STATUS}")

    place(ISSUE)
    if INCLUDE_SUB_ISSUES:
        for child in team.sub_issues(ISSUE):
            place(child["number"])


DISPATCH = {"stamp": stamp, "kind": kind, "status": status}

if MODE not in DISPATCH:
    team.fail(f"MODE must be one of {sorted(DISPATCH)}, got {MODE!r}")
DISPATCH[MODE]()
