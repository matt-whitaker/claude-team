#!/usr/bin/env python3
"""Phase 2: after a task lands, start the next one. The story carries itself from one trigger.

⚠️ DISPATCH IS A LABEL ADD, NOTHING MORE. This runs with an App-minted token whose entire grant is
issues:write on this repository — it presses the same `@claude` button the maintainer presses, and
the existing front door does everything else. No new entry path, no workflow_dispatch, no run
started any way a human could not have started it.

⚠️ THE `@claude` LABEL IS ALSO THE IN-FLIGHT MARKER. GitHub fires `labeled` only when a label is
actually added, so a task already carrying it cannot be double-dispatched — re-adding is a silent
no-op. That same mechanic is the no-retry-loop guarantee: this hook only ever labels open tasks in
the current wave that do NOT yet carry the label, so a failed task (which stays open, labelled)
halts its wave until a human intervenes. The failure capture and report already point them there.

⚠️ SEQUENCING COMES FROM THE ARCHITECT'S SECTION ON THE STORY, with the derived order as the
fallback. A numbered line is a wave; several refs on one line run in parallel:

    ### Sequencing
    1. #1050
    2. #1051, #1052 — parallel
    3. #1053

Tasks the section forgot are appended AFTER it, in derived (phase, number) order — a forgotten
task must never be stranded, and silently skipping it would be the channel-with-no-reader shape.
Refs that are not this story's tasks are dropped with a warning.

⚠️ NEVER FAILS. The cascade is a convenience over the manual gesture: if anything here breaks, the
maintainer can still label the next task by hand, exactly as before. A red cascade step after a
green landing would read as a failed run, which it is not.
"""

from __future__ import annotations

import os
import re

import team

STORY = os.environ.get("STORY", "")
HAVE_SECRETS = os.environ.get("HAVE_SECRETS", "").lower() == "true"

# ⚠️ THE MISSING TOKEN IS DIAGNOSED HERE, NOT GATED AWAY IN THE WORKFLOW. The dispatch step used
# to require a non-empty token in its `if:`, so a mint that FAILED produced a silently skipped
# step — and `continue-on-error` on the mint reports `conclusion: success`, so from outside a
# broken cascade and a deliberately-dark one looked identical. Measured on run 31928714016: every
# step green, #1093 landed and closed, #1094 never started, nothing anywhere said why.
#
# ⚠️ THE TWO CASES NEED DIFFERENT VOLUMES, which is the whole reason this is a branch and not a
# single warning. No secrets is the CONFIGURED-OFF state and must stay quiet; secrets present but
# no token is a MISCONFIGURATION that only a human can fix, and it must be loud.
if not team.GH_TOKEN:
    if HAVE_SECRETS:
        print(
            "::error::the dispatch App secrets are set but no token was minted — the App is "
            "almost certainly not INSTALLED on this repository. The mint step's 404 is "
            "`get-a-repository-installation-for-the-authenticated-app`, which means authenticated "
            "as the App but not installed here. The next task will NOT start on its own; label it "
            "by hand, then install the App to restore the cascade."
        )
    else:
        print(
            "::notice::cascade dark — no dispatch App secrets configured. The next task must be "
            "labelled by hand. This is the configured-off state, not a failure."
        )
    raise SystemExit(0)

if not team.REPO:
    team.warn("REPO is not set — nothing dispatched.")
    raise SystemExit(0)

if not STORY:
    print("no story in scope — nothing to dispatch.")
    raise SystemExit(0)

if team.issue_state(STORY) != "OPEN":
    print(f"#{STORY} is not open — nothing to dispatch.")
    raise SystemExit(0)

tasks = team.sub_issues(STORY)
if not tasks:
    print(f"#{STORY} has no tasks — nothing to dispatch.")
    raise SystemExit(0)

by_number = {int(t["number"]): t for t in tasks}


def phase(role: str) -> int:
    return {"writer": 1, "tester": 3}.get(role, 2)


def derived_order() -> list[int]:
    rows = []
    for task in tasks:
        role = team.role_stamp(team.issue_body(task["number"]))
        rows.append((phase(role), int(task["number"])))
    rows.sort()
    return [n for _, n in rows]


def sequencing_waves(body: str) -> list[list[int]]:
    """Waves from the Architect's section; the derived order, one task per wave, without one."""
    match = re.search(r"(?im)^(?:#{2,4}\s*sequencing\b|\*\*sequencing[.:]?\*\*)", body)
    waves: list[list[int]] = []
    if match:
        seen: set[int] = set()
        for line in body[match.end():].splitlines():
            if re.match(r"^#{1,6}\s", line):
                break
            if not re.match(r"^\s*\d+[.)]", line):
                continue
            refs = [int(n) for n in re.findall(r"#(\d+)", line)]
            wave = []
            for n in refs:
                if n not in by_number:
                    team.warn(f"sequencing names #{n}, which is not one of #{STORY}'s tasks — dropped.")
                elif n not in seen:
                    seen.add(n)
                    wave.append(n)
            if wave:
                waves.append(wave)
        # ⚠️ A task the section forgot is appended, never stranded.
        for n in derived_order():
            if n not in seen:
                waves.append([n])
    if not waves:
        waves = [[n] for n in derived_order()]
    return waves


waves = sequencing_waves(team.issue_body(STORY))

for wave in waves:
    states = {n: (by_number[n].get("state") or "").lower() for n in wave}
    if all(s == "closed" for s in states.values()):
        continue
    open_tasks = [n for n, s in states.items() if s != "closed"]
    to_dispatch = []
    for n in open_tasks:
        labels = {(l.get("name") or "") for l in (team.issue(n, "labels").get("labels") or [])}
        if "@claude" in labels:
            print(f"#{n} already carries @claude — in flight or awaiting a human; not re-dispatched.")
        else:
            to_dispatch.append(n)
    for n in to_dispatch:
        if team.gh("api", f"repos/{team.REPO}/issues/{n}/labels", "-f", "labels[]=@claude") is None:
            team.warn(f"could not dispatch #{n} — label it by hand to continue the story.")
        else:
            print(f"dispatched #{n} — the front door takes it from here.")
    if not to_dispatch and not open_tasks:
        continue
    # the earliest incomplete wave is the only one that dispatches; later waves wait their turn
    raise SystemExit(0)

print(f"every task of #{STORY} is closed — the story PR step handles the rest.")
