#!/usr/bin/env python3
"""The release pins: read them, set them, check them. Stdlib only, no network.

⚠️ **THE PINS ARE ONE FACT WRITTEN IN FIVE PLACES.** A release that moves one without the rest
ships a workflow fetching its assets from a different version of itself. This module is where
that list lives; the suite asserts *against* it rather than restating it, because a second copy
of the list is a second thing to forget when a sixth pin appears.

⚠️ **THIS TOOL DOES NOT RELEASE.** It edits a working tree and prints what it changed. Making
the commit and pushing the tag are the maintainer's, and nothing here does either.

⚠️ **`.github/workflows/claude.yml` IS NOT ONE OF THESE.** That is this repo's own consumer
stub. It pins a release in an ordinary PR *after* the tag exists — the same bump every consumer
makes — so flipping it with the rest would put a `vN` on mainline, which is the whole defect the
never-merged release commit exists to avoid. A test asserts this tool leaves it alone.

⚠️ **A SUBSTITUTION THAT MATCHES NOTHING PRINTS SUCCESS.** Every site is counted before it is
written and the write is refused unless the counts agree, so a pattern that drifts away from its
file fails loudly instead of leaving that pin behind.

    release_pins.py check v4.4    # assert every pin is v4.4; annotate and exit 1 if not
    release_pins.py set   v4.4    # rewrite every pin to v4.4, in the working tree
    release_pins.py steps v4.4    # print the exact commands that cut v4.4
    release_pins.py check mainline

`check` is what runs against a cut tag, where the pins must equal the tag's own name. On mainline
they are all `mainline`, and the suite's own agreement check covers that — a tag is the only place
the required value is something the repo cannot know from its contents alone.
"""
from __future__ import annotations

import pathlib
import re
import sys

# Each pattern captures the ref as `ref` and everything that must survive around it as `pre`
# (and `post` where the ref is not at the end), so a substitution rewrites the ref alone and
# leaves the rest of the line byte-identical.
PINS = (
    (".github/workflows/team.yml",
     re.compile(r"(?m)^(?P<pre>\s*TEAM_REF:\s*)(?P<ref>\S+)$"),
     "what the jobs clone at run time"),
    (".github/workflows/team.yml",
     re.compile(r"(?P<pre>uses: matt-whitaker/claude-team/\.github/actions/[^@\s]+@)(?P<ref>\S+)"),
     "the composite actions team.yml calls"),
    (".github/actions/load-prompt/action.yml",
     re.compile(r"(?P<pre>ref:\n    description[^\n]*\n    required: false\n    default: )"
                r"(?P<ref>\S+)"),
     "load-prompt's default ref"),
    ("templates/consumer-stub.yml",
     re.compile(r"(?P<pre>uses: matt-whitaker/claude-team/\.github/workflows/team\.yml@)"
                r"(?P<ref>\S+)"),
     "the stub a consumer installs"),
    ("rules/claude-team.md",
     re.compile(r"(?P<pre>\*\*team-ref: )(?P<ref>[^*\s]+)(?P<post>\*\*)"),
     "the team-ref a session reads from the clone"),
)

# What this repo pins: a release, or the edge that mainline sits at between releases.
VALID_REF = re.compile(r"^(mainline|v\d+(\.\d+)*)$")
DEFAULT_BRANCH = "mainline"

# ⚠️ THE HANDOVER BLOCK, AND THE ONLY ONE. A session cannot run a release, so it cannot test a
# release procedure — commands it composes from memory are unverified text shaped like a runbook.
# Every line below is here because a hand-written version got it wrong and the tag did not move.
STEPS = """\
# Cut {ref}. Base: origin/{base}. Run these one at a time, in this order.
# ⚠️ Not joined with && — a failure must stop where it happened, not scroll past.

git fetch origin --tags --prune --prune-tags      # a stale local tag is what silently re-pushes
git tag -d {ref} 2>/dev/null || true              # drop the local tag; `git tag` refuses to replace one
git push origin :refs/tags/{ref}                  # drop the remote tag (skip if this is a first cut)

git checkout --detach origin/{base}               # ⚠️ origin/{base}, never {base}: local may be behind
python3 scripts/release_pins.py set {ref}
python3 scripts/release_pins.py check {ref}       # ⚠️ must print "every pin is '{ref}'." before you commit

git commit -am "Release {ref}"
git tag {ref}
git push origin {ref}

# Verify the tag actually moved. This is the step whose absence hid the last three failures:
git ls-remote --tags origin refs/tags/{ref}       # sha must equal the commit you just made
git rev-parse HEAD

# Then: the Release check workflow runs on the tag. It must be green before anything upgrades.
# Then: return to {base} — `git checkout {base}` — the release commit NEVER merges.
"""


class PinMissing(LookupError):
    """A site matched nothing. The pattern has drifted from the file — fix this module."""


def read(root: pathlib.Path) -> list[tuple[str, str, str]]:
    """Every pin as (path, what it is, ref), one entry per occurrence."""
    found: list[tuple[str, str, str]] = []
    for rel, pattern, what in PINS:
        text = (root / rel).read_text(encoding="utf-8")
        refs = [m.group("ref") for m in pattern.finditer(text)]
        if not refs:
            raise PinMissing(f"{rel}: nothing matched for {what!r}. The pattern in "
                             "scripts/release_pins.py has drifted from the file.")
        found.extend((rel, what, ref) for ref in refs)
    return found


def disagree(root: pathlib.Path, expected: str) -> list[tuple[str, str, str, int]]:
    """Pins that are not `expected`, as (path, what it is, found, how many)."""
    tally: dict[tuple[str, str, str], int] = {}
    for rel, what, ref in read(root):
        if ref != expected:
            tally[(rel, what, ref)] = tally.get((rel, what, ref), 0) + 1
    return [(rel, what, ref, n) for (rel, what, ref), n in tally.items()]


def set_ref(root: pathlib.Path, ref: str) -> list[tuple[str, str, int]]:
    """Rewrite every pin to `ref`. Returns (path, what it is, how many) per site."""
    if not VALID_REF.match(ref):
        raise ValueError(f"{ref!r} is not a ref this repo pins — a release like 'v4.4', "
                         "or 'mainline'.")
    written: list[tuple[str, str, int]] = []
    for rel, pattern, what in PINS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        expected = sum(1 for _ in pattern.finditer(text))
        if not expected:
            raise PinMissing(f"{rel}: nothing matched for {what!r}. The pattern in "
                             "scripts/release_pins.py has drifted from the file.")
        new, count = pattern.subn(
            lambda m: m.group("pre") + ref + (m.groupdict().get("post") or ""), text)
        if count != expected:
            raise AssertionError(f"{rel}: rewrote {count} of {expected} — refusing to leave a "
                                 "partial edit behind.")
        if new != text:
            path.write_text(new, encoding="utf-8")
        written.append((rel, what, count))
    return written


def main(argv: list[str]) -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    if len(argv) != 3 or argv[1] not in ("check", "set", "steps"):
        print("usage: release_pins.py check <ref>   assert every pin equals <ref>")
        print("       release_pins.py set   <ref>   rewrite every pin to <ref>")
        print("       release_pins.py steps <ref>   print the exact commands to cut <ref>")
        return 2
    command, ref = argv[1], argv[2]

    try:
        return run(root, command, ref)
    except (PinMissing, ValueError, AssertionError) as exc:
        print(f"::error::{exc}")
        return 1


def run(root: pathlib.Path, command: str, ref: str) -> int:
    if command == "check":
        wrong = disagree(root, ref)
        for rel, what, found, n in sorted(wrong):
            where = f"{n} places in {rel}" if n > 1 else rel
            print(f"::error::{where} pins {found!r}, expected {ref!r} — {what}")
        if wrong:
            total = sum(n for *_, n in wrong)
            print(f"{total} pin(s) disagree with {ref!r}. A tag whose pins are not its own name "
                  "makes every consumer fetch a different version at run time.")
            return 1
        print(f"every pin is {ref!r}.")
        return 0

    if command == "steps":
        if not VALID_REF.match(ref):
            raise ValueError(f"{ref!r} is not a ref this repo pins — a release like 'v4.4'.")
        print(STEPS.format(ref=ref, base=DEFAULT_BRANCH))
        return 0

    for rel, what, count in set_ref(root, ref):
        print(f"{rel}: {count} -> {ref}  ({what})")
    print("Nothing is committed and no tag is pushed; both are yours. "
          "`.github/workflows/claude.yml` is deliberately untouched — it moves after the tag.")
    print(f"\nRemaining steps: python3 scripts/release_pins.py steps {ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
