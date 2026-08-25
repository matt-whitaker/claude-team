---
name: upgrade-team
description: Bring an already-installed claude-team consumer up to the current version — bump the pin, reconcile the stub, and re-copy the half a pin cannot carry (rules, skills, labels, settings). Use when a repo running claude-team needs updating, or a session is unsure whether an install is current.
argument-hint: [target repo]
---

An installed repo drifts because the install runs once and the upgrade never does. This is the
upgrade, and `INSTALL.md` §0 is its authority — read it there; this skill is the order to work in
and the conduct around it, not a second copy of the logic.

## Detect where the target is

The pin *is* the version. There is no second number to invent.

```bash
grep -o 'team\.yml@[^ ]*' <target>/.github/workflows/claude.yml   # installed
git ls-remote --tags https://github.com/matt-whitaker/claude-team  # available
```


## The order (INSTALL.md §0 is the detail)

1. **Read `CHANGELOG.md` from the installed ref to the current tag.** Every version heading has an
   `**Action required:**` line. All `no` → only the bump and the re-copy remain.
2. **Bump the `uses:` ref, and re-fetch `rules/claude-team.md` so its `team-ref` matches it.** They
   are one fact in two places; a mismatch is the half-done upgrade nothing else can see.
3. **Reconcile the stub — never recreate it.** Diff against `templates/consumer-stub.yml`. A new
   input shows up here and nowhere else, because a consumer's stub is frozen.
4. **Leave overlays alone unless the CHANGELOG says otherwise** — except the one trap it names: an
   overlay composes after the base and wins, so a base rule that tightened a role's scope reaches
   nothing if the overlay still grants it. Grep the overlays for the old grant.
5. **Re-copy the half a pin cannot carry — every time, unconditionally.** These are committed files
   and GitHub state, so no ref bump ever touches them:
   - `.claude/rules/claude-team.md` and `.claude/rules/claude-session.md`
   - `.claude/skills/*`, `.claude/settings.json`, `.claude/hooks/guard-push.py`
   - the label loop (§4) — labels live in GitHub, not the clone
   - the board, and any secret or setting a CHANGELOG entry newly requires
6. **Drill again (in the drill repo) only if something structural moved** — a new input, a routing
   change, a changed role set. A prose release does not earn a run.

## Conduct

- **Ship it as install ships: branch → PR → merge.** Never push the target's default branch, and
  nothing takes effect until merge — `issues` events run the workflow from the default branch, so a
  workflow fix does not reach an in-flight story until the default branch carries it.
- **Report which happened**: installed, upgraded from ref N with what the CHANGELOG said to do, or
  already current. "Bumped and hoped" is the failure this skill exists to end.
