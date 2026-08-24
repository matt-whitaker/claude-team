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

SCRIPT_ROLES = os.environ.get("SCRIPT_ROLES", "")

# Only a `defaulted` route is reported — the real gap, carrying a remedy. A bare mention
# settles to the root role, which bails (epic #78); nothing to report there.
if not (NUMBER and ROLES) or not DEFAULTED:
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
