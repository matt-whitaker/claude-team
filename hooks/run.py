"""One entry point for the deterministic verbs, so both drivers invoke identical code.

A CI step runs a hook as `python3 hooks/<name>.py` with its inputs in env. A session driving a
story needs the same verbs against its own checkout — and "find the right script and remember its
name" is exactly the kind of instruction that gets half-remembered. This dispatcher makes the
verb set discoverable and the invocation uniform:

    python3 hooks/run.py --list          # every verb, with what it does
    ISSUE=72 python3 hooks/run.py work-completion

It adds NO behaviour: a verb is a hook script, executed with the caller's env, exiting with the
hook's own exit code. Inputs stay env vars — the contract the hooks already have — so nothing
here parses arguments on a hook's behalf.

⚠️ Verbs are derived from the directory listing, never enumerated here. This package already
learned that a hand-kept roster of its own parts drifts (four role enumerations, no two agreeing
— see the epic on role opt-in). `team.py` is the library and this file is the dispatcher; both
are excluded because neither is a verb.

⚠️ An unknown verb fails NAMING THE KNOWN SET. Failing loudly is not the same as failing
usefully (RULES.md E8): the caller who typo'd a verb should not need a second command to learn
what was available.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
NOT_VERBS = {"run.py", "team.py"}


def verbs() -> dict[str, str]:
    """Verb name -> first docstring line, derived from the directory."""
    found = {}
    for script in sorted(HERE.glob("*.py")):
        if script.name in NOT_VERBS:
            continue
        summary = ""
        for line in script.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(('"""', "'''")):
                summary = line.strip("\"'").strip()
                break
        found[script.stem] = summary
    return found


def main(argv: list[str]) -> int:
    known = verbs()
    if not argv or argv[0] in ("--list", "-l"):
        width = max(len(v) for v in known)
        for name, summary in known.items():
            print(f"{name:<{width}}  {summary}")
        return 0
    verb = argv[0]
    if verb not in known:
        print(f"unknown verb: {verb}", file=sys.stderr)
        print(f"known: {', '.join(known)}", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(HERE / f"{verb}.py"), *argv[1:]]).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
