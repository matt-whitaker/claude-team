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
ordinary quote under `str.split()`. Real lexing is what closes it, and both failure directions
have the same root: without real tokenization there is no notion of an argument boundary, so a
quoted branch name reads as a different branch and a command *described inside* an issue body
reads as that command being run.

⚠️ **GROUPING SYNTAX WRAPS A COMMAND; IT IS NOT ONE.** bash splits a leading `(` off as its own
operator before the word `git`, and `shlex.split()` does not — it returns the parenthesis glued
onto that word. The first token then matches neither the program nor a prefix, so every check
below is skipped while bash runs `(git push origin mainline)` exactly as written. `punctuation_chars`
makes the lexer split the characters bash treats as operators, and grouping tokens are then dropped
the same way `sudo` or an env assignment is. The closing character is the same failure at the other
end: `(cd /tmp && git push origin mainline)` leaves `mainline)` as the target, and a token compared
against a set of whole refs no longer matches one.

⚠️ **The lexer must carry no comment character.** `shlex.shlex` defaults to treating `#` as one
where `shlex.split()` does not, and every token after a `#` would vanish — an issue reference, a
colour, a URL fragment — leaving the guard to inspect a command that stops early.

⚠️ **SEGMENTING AND TOKENIZING ARE ONE PASS, AND THE LEXER DOES BOTH.** Splitting the raw line
into commands before anything knows what is quoted gets both directions wrong at once, and the
same regex is responsible for each. It cannot see that a separator is *inside* an argument, so
`probe 'echo hi; git push origin mainline'` is cut in two and the right-hand piece — text a
function was handed — is inspected as an invocation. And it cannot see that a **newline** ends a
command, so `echo hi` above a push collapses into one segment whose first word is `echo` and
everything below it is unreachable. A two-line Bash call is the ordinary shape, not an
adversarial one. The lexer knows quoting and it knows operators, so it produces the boundaries:
split the token stream on the separator tokens it emitted, never the string on a pattern.

⚠️ **A newline is an operator here, not whitespace.** `shlex` counts it as whitespace by default
and would discard it, which is the same as not splitting on it at all.

⚠️ **A heredoc body reads as commands, and that cost is accepted.** `shlex` has no notion of
`<<EOF`, so a line inside one beginning with `git push` is a segment like any other and writing
that file through the shell is refused. The only way to avoid it is to stop splitting on
newlines, which is the bypass above — so the body is over-matched on purpose. Write such a file
with a tool that is not the shell.

⚠️ **Match on position, never on co-presence.** `gh pr merge` is a program and two subcommands in
sequence; three trigger words appearing somewhere in a line is a sentence. Reading co-presence
blocks `gh issue create --body "...gh pr merge..."` — filing a report about this guard — which is
the false-positive mirror of the bypass and cost exactly as much.

⚠️ **Token-match, never substring**: a branch named `42-mainline-fix` must not trip the `mainline`
rule. Push targets are compared as whole refs after splitting refspecs on `:`.

⚠️ **`shlex` LEXES; IT DOES NOT EXPAND.** `$BRANCH`, `${BRANCH}` and `$(...)` reach git as
whatever bash resolved them to, which this guard cannot know — so a push target carrying one is
refused rather than cleared. That is the one place it fails closed on a command it parsed
successfully, and it is narrow on purpose: only the target of a push, where being wrong means the
default branch.

⚠️ **A tokenizer failure is not a licence.** An unbalanced quote makes `shlex` raise, and standing
down there would hand back every bypass this docstring describes: a trailing `"` is the shortest
one to type. The approximation drops quote characters and spaces the operators out itself, which
over-matches rather than under-matches. Only a malformed *event* fails open — that is the harness
changing shape, not a command evading a check.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

DEFAULT_BRANCHES = {"mainline", "main", "master"}
# Flags that push refs without naming any: --all sends every local branch, the default one
# among them; --mirror also deletes remote refs the local clone does not have.
UNTARGETED_PUSH = ("--all", "--mirror")
# A token the shell would expand before git sees it. shlex lexes, it does not evaluate.
UNRESOLVED = ("$", "`")
# Prefixes that precede the real command without being it.
PREFIXES = {"sudo", "command", "env", "nohup", "time", "exec", "builtin"}
# bash grouping. A subshell or brace group stands around a command without being part of it, at
# either end — the opener hides the program name, the closer rides on the push target.
GROUPING = {"(", ")", "{", "}"}
# Characters that end one simple command and begin the next. ⚠️ Matched by COMPOSITION, not
# against a list of operators: the lexer fuses a run of them into one token, so `&&`, `;;`, a
# blank line (`\n\n`) and `;\n` all arrive as single tokens no enumeration would hold.
SEPARATOR_CHARS = frozenset(";&|\n")
# What the lexer is told to treat as operators rather than word characters.
PUNCTUATION = "();<>|&\n"
OPERATOR_CHARS = frozenset(PUNCTUATION)
# The same operators for the approximation, longest first so `&&` never reads as two `&`.
APPROX_OPERATORS = re.compile(r"&&|\|\||;;|[();{}|&<>]")
# git's own global flags that consume the following token as their value.
GIT_VALUE_FLAGS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*=")


def deny(reason: str) -> None:
    print(reason, file=sys.stderr)
    sys.exit(2)


def approximate(command: str) -> list[str]:
    """Over-matching tokens for a line the lexer will not parse. Quote characters are dropped
    rather than honoured, and a newline becomes a separator, so an unbalanced quote widens what
    is inspected instead of hiding it."""
    flat = command.replace('"', " ").replace("'", " ").replace("\n", " ; ")
    return APPROX_OPERATORS.sub(lambda m: f" {m.group(0)} ", flat).split()


def operators(token: str) -> list[str]:
    """Split a fused run of operator characters into the operators bash reads.

    ⚠️ The lexer returns adjacent operator characters as ONE token, so `$(…); rc=$?` yields
    `);` — which is neither a separator nor grouping, so the command never ends and whatever
    follows is read as an argument to it. Splitting at each separator/non-separator boundary
    gives back `)` and `;`, and leaves genuine pairs like `&&` and a blank line intact."""
    parts: list[str] = []
    current = ""
    for char in token:
        if current and (char in SEPARATOR_CHARS) != (current[-1] in SEPARATOR_CHARS):
            parts.append(current)
            current = ""
        current += char
    if current:
        parts.append(current)
    return parts


def segments(command: str) -> list[list[str]]:
    """Every simple command in the line, tokenized the way the shell would tokenize it."""
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=PUNCTUATION)
        lex.whitespace = " \t\r"
        lex.whitespace_split = True
        lex.commenters = ""
        tokens = list(lex)
    except ValueError:
        tokens = approximate(command)
    expanded: list[str] = []
    for token in tokens:
        if token and not (set(token) - OPERATOR_CHARS):
            expanded.extend(operators(token))
        else:
            expanded.append(token)
    found: list[list[str]] = []
    current: list[str] = []
    for token in expanded:
        if token and not (set(token) - SEPARATOR_CHARS):
            if current:
                found.append(current)
            current = []
        else:
            current.append(token)
    if current:
        found.append(current)
    return found


def command_tokens(tokens: list[str]) -> list[str]:
    """Drop leading env assignments, grouping syntax and prefix programs so tokens[0] is the
    command itself."""
    i = 0
    while i < len(tokens) and (ASSIGNMENT.match(tokens[i]) or tokens[i] in PREFIXES
                               or tokens[i] in GROUPING):
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

    # Examine each simple command in a compound line.
    for segment in segments(command):
        tokens = command_tokens(segment)
        if not tokens:
            continue

        if tokens[0] == "git":
            sub = git_subcommand(tokens)
            if sub is not None and tokens[sub] == "push":
                rest = [t for t in tokens[sub + 1:] if t not in GROUPING]
                if any(t in ("--force", "-f") or t.startswith("--force-with-lease")
                       or t.startswith("--force-if-includes") for t in rest):
                    deny("guard-push: force-push is blocked here — reconcile by merge, or hand "
                         "the conflict to the maintainer. (claude-team guard)")
                if any(t in UNTARGETED_PUSH for t in rest):
                    deny("guard-push: --all and --mirror push the default branch without naming "
                         "it, and --mirror deletes remote refs. Push one branch by name. "
                         "(claude-team guard)")
                for t in rest:
                    if t.startswith("-"):
                        continue
                    # ⚠️ `+ref` is git's OWN force shorthand: it strips the `+`, then parses the
                    # rest as `src[:dst]`. It carries no force flag, so the check above cannot
                    # see it, and the `+` survives into the comparison below unless stripped —
                    # which is how one character defeated both invariants at once.
                    if t.startswith("+"):
                        deny("guard-push: '+' before a refspec is a force-push — reconcile by "
                             "merge, or hand the conflict to the maintainer. (claude-team guard)")
                    # a refspec pushes to its right-hand side; a bare ref pushes to itself
                    target = t.split(":")[-1]
                    # ⚠️ An unexpanded token is one the guard FAILED TO READ, not one it cleared.
                    # bash resolves `$BRANCH` before git sees it; shlex does not. Refusing is the
                    # only honest answer, and a literal ref costs the caller nothing.
                    if any(c in target for c in UNRESOLVED):
                        deny(f"guard-push: '{target}' expands at run time and this guard cannot "
                             "read it, so it cannot clear it. Write the ref literally. "
                             "(claude-team guard)")
                    if target.removeprefix("refs/heads/") in DEFAULT_BRANCHES:
                        deny(f"guard-push: pushing to '{target}' is blocked — the default branch "
                             "changes by merged PR only. Push a branch and open the PR. "
                             "(claude-team guard)")

        if tokens[0] == "gh":
            # gh's own flags may precede the subcommand pair; the pair itself is adjacent.
            words = [t for t in tokens[1:] if not t.startswith("-") and t not in GROUPING]
            if any(a == "pr" and b == "merge" for a, b in zip(words, words[1:])):
                deny("guard-push: merging is the maintainer's — open or update the PR and hand "
                     "over the link. (claude-team guard)")

    sys.exit(0)


if __name__ == "__main__":
    main()
