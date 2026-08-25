#!/usr/bin/env python3
"""PreToolUse guard: no push to the default branch, no force-push, no merge — from any driver.

Installed into a consumer's `.claude/hooks/` beside the settings fragment that wires it. The
harness runs it before every Bash tool call; exit 2 blocks the call and the message on stderr
reaches the model. Stdlib only, no network — a guard that can fail on a fetch is a guard that
gets skipped.

⚠️ This is law, not procedure: the same rules exist as prompt instructions, and the record of
this package is that instructions get skipped (E17). The guard is what makes "never push the
default branch" true of a session the way the workflow's permissions make it true of CI.

⚠️ Token-match, never substring: a branch named `42-mainline-fix` must not trip the `mainline`
rule. Push targets are compared as whole refs after splitting refspecs on `:`.
"""
import json
import re
import sys

DEFAULT_BRANCHES = {"mainline", "main", "master"}


def deny(reason: str) -> None:
    print(reason, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # not our shape; never block on our own parse failure
    command = (event.get("tool_input") or {}).get("command") or ""
    if not command:
        sys.exit(0)

    # Normalise: examine each simple command in a compound line.
    for part in re.split(r"(?:&&|\|\||;|\|)", command):
        tokens = part.strip().split()
        if not tokens:
            continue

        if "git" in tokens[:2] and "push" in tokens:
            rest = tokens[tokens.index("push") + 1:]
            if any(t in ("--force", "-f") or t.startswith("--force-with-lease") for t in rest):
                deny("guard-push: force-push is blocked here — reconcile by merge, or hand the "
                     "conflict to the maintainer. (claude-team guard)")
            for t in rest:
                if t.startswith("-"):
                    continue
                # a refspec pushes to its right-hand side; a bare ref pushes to itself
                target = t.split(":")[-1]
                if target.removeprefix("refs/heads/") in DEFAULT_BRANCHES:
                    deny(f"guard-push: pushing to '{target}' is blocked — the default branch "
                         "changes by merged PR only. Push a branch and open the PR. "
                         "(claude-team guard)")

        if "gh" in tokens[:1] and "pr" in tokens and "merge" in tokens:
            deny("guard-push: merging is the maintainer's — open or update the PR and hand over "
                 "the link. (claude-team guard)")

    sys.exit(0)


if __name__ == "__main__":
    main()
