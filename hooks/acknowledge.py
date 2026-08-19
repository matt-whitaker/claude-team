#!/usr/bin/env python3
"""The delegate job's first step. Reacts 👀 so the maintainer knows the trigger landed
before any model has thought about it.

Scripted, not prompted. An acknowledgement a model can forget is worse than none — the
silence reads identically to "nothing happened", which is the state it exists to rule out.
"""

import os

import team

COMMENT_ID = os.environ.get("COMMENT_ID", "")
NUMBER = os.environ.get("NUMBER", "")

if not team.REPO:
    team.fail("REPO is required")

# Reacts to the comment when one triggered the run, otherwise to the issue itself, so the
# 👀 appears where the maintainer is looking.
#
# The comment id must come from an `issue_comment` event only. A *review* comment's id
# belongs to the pulls collection, and reacting to it through issues/comments would hit an
# unrelated comment or 404. Empty falls back to the issue or PR, which is always right.
if COMMENT_ID:
    target, what = f"repos/{team.REPO}/issues/comments/{COMMENT_ID}/reactions", f"comment {COMMENT_ID}"
elif NUMBER:
    target, what = f"repos/{team.REPO}/issues/{NUMBER}/reactions", f"#{NUMBER}"
else:
    print("No comment or issue to acknowledge.")
    raise SystemExit(0)

if team.gh("api", target, "-f", "content=eyes") is not None:
    print(f"👀 -> {what}")
else:
    team.warn(f"could not react to {what}")
