#!/usr/bin/env python3
"""PreToolUse guard: no push to the default branch, no force-push, no merge — from any driver.

Installed into a consumer's `.claude/hooks/` beside the settings fragment that wires it. The
harness runs it before every Bash tool call; exit 2 blocks the call and the message on stderr
reaches the model. Stdlib only, no network — a guard that can fail on a fetch is a guard that
gets skipped.

⚠️ This is law, not procedure: the same rules exist as prompt instructions, and the record of
this package is that instructions get skipped (E17). The guard is what makes "never push the
default branch" true of a session the way the workflow's permissions make it true of CI.

⚠️ **TOKENIZE THE WAY THE SHELL DOES, OR THE GUARD MATCHES A DIFFERENT COMMAND THAN THE ONE THAT
RUNS.** bash strips quotes before `git` ever sees an argument, so `git push origin "mainline"`
executes identically to the bare form — but a whitespace split sees the token `"mainline"`, which
is not the word in the set, and the guard stands down. Every protection here is defeated by one
ordinary quote under `str.split()`. `shlex.split()` is what closes it, and both failure directions
have the same root: without real tokenization there is no notion of an argument boundary, so a
quoted branch name reads as a different branch and a command *described inside* an issue body
reads as that command being run.

⚠️ **Match on position, never on co-presence.** `gh pr merge` is a program and two subcommands in
sequence; three trigger words appearing somewhere in a line is a sentence. Reading co-presence
blocks `gh issue create --body "...gh pr merge..."` — filing a report about this guard — which is
the false-positive mirror of the bypass and cost exactly as much.

⚠️ **Token-match, never substring**: a branch named `42-mainline-fix` must not trip the `mainline`
rule. Push targets are compared as whole refs after splitting refspecs on `:`.

⚠️ **A tokenizer failure is not a licence.** An unbalanced quote makes `shlex` raise, and standing
down there would hand back every bypass this docstring describes: a trailing `"` is the shortest
one to type. The fallback strips quote characters and splits, which over-matches rather than
under-matches. Only a malformed *event* fails open — that is the harness changing shape, not a
command evading a check.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

DEFAULT_BRANCHES = {"mainline", "main", "master"}
# Prefixes that precede the real command without being it.
PREFIXES = {"sudo", "command", "env", "nohup", "time", "exec", "builtin"}
# git's own global flags that consume the following token as their value.
GIT_VALUE_FLAGS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*=")


def deny(reason: str) -> None:
    print(reason, file=sys.stderr)
    sys.exit(2)


def tokenize(segment: str) -> list[str]:
    """Shell-accurate tokens, or an over-matching approximation when the line will not parse."""
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.replace('"', " ").replace("'", " ").split()


def command_tokens(tokens: list[str]) -> list[str]:
    """Drop leading env assignments and prefix programs so tokens[0] is the command itself."""
    i = 0
    while i < len(tokens) and (ASSIGNMENT.match(tokens[i]) or tokens[i] in PREFIXES):
        i += 1
    return tokens[i:]


def git_subcommand(tokens: list[str]) -> int | None:
    """Index of git's subcommand, past its global flags. None if the line names none."""
    i = 1
    while i < len(tokens):
        t = tokens[i]
        if t in GIT_VALUE_FLAGS:
            i += 2
        elif t.startswith("-"):
            i += 1
        else:
            return i
    return None


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
        tokens = command_tokens(tokenize(part))
        if not tokens:
            continue

        if tokens[0] == "git":
            sub = git_subcommand(tokens)
            if sub is not None and tokens[sub] == "push":
                rest = tokens[sub + 1:]
                if any(t in ("--force", "-f") or t.startswith("--force-with-lease")
                       or t.startswith("--force-if-includes") for t in rest):
                    deny("guard-push: force-push is blocked here — reconcile by merge, or hand "
                         "the conflict to the maintainer. (claude-team guard)")
                for t in rest:
                    if t.startswith("-"):
                        continue
                    # a refspec pushes to its right-hand side; a bare ref pushes to itself
                    target = t.split(":")[-1]
                    if target.removeprefix("refs/heads/") in DEFAULT_BRANCHES:
                        deny(f"guard-push: pushing to '{target}' is blocked — the default branch "
                             "changes by merged PR only. Push a branch and open the PR. "
                             "(claude-team guard)")

        if tokens[0] == "gh":
            # gh's own flags may precede the subcommand pair; the pair itself is adjacent.
            words = [t for t in tokens[1:] if not t.startswith("-")]
            if any(a == "pr" and b == "merge" for a, b in zip(words, words[1:])):
                deny("guard-push: merging is the maintainer's — open or update the PR and hand "
                     "over the link. (claude-team guard)")

    sys.exit(0)


if __name__ == "__main__":
    main()
