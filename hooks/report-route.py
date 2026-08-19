#!/usr/bin/env python3
"""Says, where the maintainer looks, that this run did not route from state alone.

⚠️ THIS EXISTS BECAUSE `defaulted` WAS A CHANNEL WITH NO READER. It was emitted to
`$GITHUB_OUTPUT` and declared as a job output for a long time with nothing consuming it — so
"default rather than stall, but say so" said so only in a log nobody opens. That is the same shape
that shipped dead for the #475/#476 handoff, for `decisions` on the PR path, and for
`docsCandidates` (#797).

⚠️ IT RUNS AFTER THE INTERCEPTION, not inside `delegate.py`, and the ordering is the whole point.
The script announcing its own default announces it before the root role has been asked — so an
intercepted route posted "I guessed" and then ran something else entirely. A notice describing a
decision that did not take effect is worse than none: it is a false record of why the run did what
it did (#798).

⚠️ ONE COMMENT, UPSERTED, and the two outcomes share its marker deliberately. A re-run that
resolves the same way twice is one fact, not two — unlike the decisions log, where each round is
its own record. Sharing the marker is also what makes a later interception *replace* an earlier
guess rather than sit under it.

⚠️ THE REMEDY SURVIVES BOTH OUTCOMES. Deciding correctly does not repair the issue: the stamp is
still missing and the next trigger lands in the same fallback. A notice the reader cannot act on
is noise, and this one is only ever raised where the fix is a single line.
"""

import os

import team

NUMBER = os.environ.get("NUMBER", "")
DEFAULTED = os.environ.get("DEFAULTED", "") == "true"
ROLES = os.environ.get("ROLES", "")
REASON = os.environ.get("REASON", "")
REMEDY = os.environ.get("REMEDY", "")
RESOLVED_BY = os.environ.get("RESOLVED_BY", "script")

MARKER = "<!-- claude-team:routing-guess -->"

if not team.REPO:
    team.fail("REPO is required")

CONSULT = os.environ.get("CONSULT", "") == "true"
SCRIPT_ROLES = os.environ.get("SCRIPT_ROLES", "")

if not (NUMBER and ROLES) or not (DEFAULTED or CONSULT):
    raise SystemExit(0)

# ⚠️ A CONSULTATION IS NOT A GAP, AND MOST OF THEM DESERVE SILENCE. `defaulted` means the state
# that should have decided is missing — worth announcing, and it carries a remedy. `consult` means
# somebody typed `@claude` and the only open question was whether they wanted words or work. When
# the answer is "words", the run does exactly what it would have done anyway and there is nothing
# to report; announcing it every time would make this notice the thing people skim past.
#
# ⚠️ But when a consultation CHANGES the route, say so — that is the maintainer asking for one
# thing and getting another, correctly, and they should not have to infer it from which job ran.
if CONSULT and not DEFAULTED and ROLES == SCRIPT_ROLES:
    print(f"consulted, and the route is unchanged ({ROLES}) — nothing to report.")
    raise SystemExit(0)

if CONSULT and not DEFAULTED:
    team.upsert_comment(
        NUMBER, MARKER,
        f"{MARKER}\n🔔 **You asked `@claude`, and this reads as a request for work rather than a "
        f"question — so it was routed to `{ROLES}` instead of being answered.** {REASON}\n\n"
        f"If you wanted an answer rather than the work, say so and it will not route again."
        + team.run_footer(),
    )
    raise SystemExit(0)

if RESOLVED_BY == "custodian":
    body = (
        f"🔔 **The router could not settle this one, so I read the issue and picked a role.** "
        f"Running `{ROLES}` — {REASON}.\n\n"
        f"{REMEDY}\n\n"
        "Until then every trigger on this issue takes the same detour, which works but costs a "
        "run before any of the work starts."
    )
else:
    body = (
        f"🔔 **I guessed the role for this one.** Routed to `{ROLES}` because {REASON}.\n\n"
        f"{REMEDY}\n\n"
        "Until then this keeps guessing the same way, which is recoverable but not right."
    )

team.upsert_comment(NUMBER, MARKER, f"{MARKER}\n{body}" + team.run_footer())
