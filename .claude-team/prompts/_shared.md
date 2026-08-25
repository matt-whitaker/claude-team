## This repository

**claude-team** — the portable Claude/GitHub role team itself: the prompts, the scripted hooks
around them, and the reusable workflow that runs them. This repo is now its own consumer, so the
machinery you are running *is* the machinery you are working on.

⚠️ **Your run executes the assets at `TEAM_REF`, never the ones in your checkout.** Editing a hook
on your branch changes nothing about the run editing it. It changes every consumer's next run the
moment it merges — here, in `claude-team-example`, and in anything else tracking `mainline`. Write
as if the change ships on merge, because it does.

## The gate

```
python3 -m compileall -q hooks
python3 -m unittest discover -s tests
```

Stdlib only. **No dependencies, no package manager, no network** — a test that needs a package is
a test that cannot run here, and reaching for one is a finding, not a fix.

⚠️ **Reading it: a green suite is not the same as a covered one.** `tests/harness.py` copies the
hook under test into a scratch directory and builds **real git repositories** for anything that
touches git. A case whose sandbox is too clean passes without exercising anything — that is this
repo's characteristic false pass, not a hypothetical (CLAUDE.md, #748: a fresh branch hid the
stale-ref arithmetic entirely, so every sandbox that built one passed).

⚠️ `.github/workflows/verify.yml` runs a third check with a 35-minute lesson behind it: **a `#`
line indented under an `if: |` block is expression text, not a comment**, and it invalidates the
whole workflow file — GitHub reports zero jobs and no log. Comments go *outside* the block.

## Invariants you could break without noticing

1. ⚠️ **Nothing under `prompts/`, `hooks/`, `schemas/` or `.github/` may name a consuming repo**,
   its branches, its gate, its packages or its paths. That is the one property that makes this
   package portable. `.claude-team/` — this overlay — is the exception and the whole point: it is
   the consumer half, and naming this repo *here* is correct.
2. ⚠️ **The pins move together.** `TEAM_REF` in `team.yml`, the `uses: matt-whitaker/claude-team/…@ref`
   refs inside it, `load-prompt`'s default `ref`, and `templates/consumer-stub.yml`'s `uses:` ref.
   `ReleasePins` asserts they agree on every push. ⚠️ `.github/workflows/claude.yml` — this repo's
   own stub — is deliberately **not** one of them: it tracks `mainline` permanently, and
   `SelfInstall` asserts that.
3. ⚠️ **Every `gh` call in a hook goes through `team.gh()` / `team.gh_json()`.** `gh api` prints
   its error body to **stdout**, so a 404 is indistinguishable from data to anything that only
   checks whether output arrived. This trap survived being documented and was written again
   anyway, twice.
4. ⚠️ **A hook doing network git calls `team.authenticate_git()` first** — the host action unsets
   the checkout's credential, so an inherited token is gone by post-hook time. Anything reporting
   git output **outside the job log** (an issue comment, a PR body) passes it through
   `team.scrub()` first: the token lives in the remote URL, git echoes that URL in its errors, and
   Actions masks secrets in the log only.
5. ⚠️ **`schemas/*.json` must contain no single quote and must survive being compacted to one
   line.** A workflow step injects it inline into `--json-schema`, single-quoted, and the argument
   list is parsed line by line.
6. **A hook must not depend on its location in this repo.** The harness copies it into a scratch
   directory beside a scripted `team` stub — Python resolves imports from the script's own
   directory before `PYTHONPATH`, which once silently shadowed that stub.

## CLAUDE.md is the design record, and it is append-mostly

Its ⚠️ paragraphs are **measured failures** — run numbers, issue numbers, what it cost — not house
style. Do not compress them, tidy them, or merge two that read alike: a pair that looks redundant
is usually two different failures that presented the same way, and the second one is why the rule
survived. A superseded rule stays, with a note saying it was tried and why it was wrong. The
obsolete branch-sweep note is kept on exactly that basis.

## Boundaries

- ⚠️ **This repo's suite does not prove a behavioural change.** It proves the hooks in isolation;
  the platform is what breaks. A change to `hooks/` or `team.yml` is drilled in
  **`claude-team-example`**, which tracks `mainline` for that reason. Say in your report what
  still needs drilling there — you cannot do it from here.
- ⚠️ **Releases are the maintainer's.** Never tag, never flip a pin from `mainline` to a `vN`, and
  never merge a release commit — `mainline` keeps its canary pins on purpose.
- ⚠️ **There is no design system and no app to drive.** No `Role: designer` task exists here and
  none should be cut; every code task is the Implementor's. The base prompts' browser-harness and
  selector guidance has no referent in this repo — ignore it rather than inventing one.
- **Secrets never pass through a run.** Anything needing one is filed for the maintainer, named
  precisely, with what breaks until it is set.

## Writing here

⚠️ **Never write the front-door label's literal handle in an issue or PR comment** — the
`@`-prefixed name of the root role. It starts a run, and **backticks do not protect it**. Write
around it: "the front-door label", "the root role's handle". The same goes for any
`@`-prefixed role handle you are describing rather than invoking.

Match the file you are editing. `CLAUDE.md` is dense, ⚠️-marked and argues from evidence;
`README.md` is short and orienting; `INSTALL.md` is a runbook a session executes without
further research. A fact in the wrong one of those three is the commonest error here.
