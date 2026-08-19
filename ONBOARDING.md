# ONBOARDING — installing the team into a repo

This is a runbook for a Claude session. Point one here together with a **target repo** and it
should produce a working install without further research. It is the sequence that onboarded
`brewdocs.beer-kb`, written down. Everything ships branch → PR — never push the target's
default branch — and the proof of the install is post-merge, because `issues` events always run
the workflow from the default branch.

Private targets are supported (since `v1.1`). Public and private differ in nothing below.

## 1. Decide the four inputs

Settle these before touching files; each is a judgment call about the target, not boilerplate.

- **`project_owner` / `project_number`** — the GitHub Projects board its issues and PRs go on.
- **`allowed_bots`** — `""` unless a dispatch App is installed on the target. Empty means the
  task cascade is **dark**: a finished task will not dispatch the next one, and the maintainer's
  label gesture drives everything. That is the correct starting state — the cascade is an
  upgrade, not a prerequisite — and the value is flipped to the App's slug later, when the App
  half of step 6 happens. ⚠️ Name the App, never `*`: a wildcard admits any App on GitHub.
- **`node`** — `true` if any author needs a runtime to install or build with; a repo whose gate
  is `npm run <anything>` wants it even with zero dependencies.
- **`browser`** — `true` only if authors must drive a running app to verify their work. Every
  author run then pays a chromium download, so a data or docs repo says `false`.

## 2. The stub

Copy [`templates/consumer-stub.yml`](templates/consumer-stub.yml) to the target's
`.github/workflows/claude.yml`, set the inputs, and **pin the `uses:` ref to the newest `vN`
tag** (`git ls-remote --tags` here answers which). One repo in the fleet deliberately tracks
`@mainline` to find breakage first; every other consumer pins, and picks up fixes by bumping
the pin in a one-line PR when a release is cut.

⚠️ **Do not trim the `permissions:` block, even if the target seems not to need parts of it.**
A called workflow cannot request permissions its caller didn't grant — the stub's block is the
ceiling the team's jobs draw down from, not a grant to the stub itself. Cutting it produces a
`startup_failure` before any job runs, fingerprinted in the run's error as
*"The nested job 'delegate' is requesting … but is only allowed …"*.

If authors need setup beyond installing dependencies, add an executable `.claude-team/setup.sh`
([`templates/setup.sh.example`](templates/setup.sh.example)); otherwise omit it.

## 3. The overlays — where the target's personality lives

Create `.claude-team/prompts/_shared.md`. This is the file that makes the install *this repo's*
team rather than a generic one, and it is prepended to every role's prompt. It carries:

- **The gate**, including how to *read* it — if the build logs-and-continues on a bad input, say
  that a clean exit with an error line in it is a red gate.
- **The invariants a role could break without noticing** — derived identifiers, load-bearing
  filenames, version stamps, unit strings.
- **The boundaries** — what this repo must never lead on (e.g. a data repo whose schema is owned
  by the app that consumes it), and where such work goes instead.

Add `<role>.md` files only where a role needs repo-specific shaping. Exemplars, in increasing
weight: [`claude-team-example`](https://github.com/matt-whitaker/claude-team-example) (minimal,
annotated for an audience), `brewdocs.beer-kb` (a research-led data repo: its Researcher overlay
redefines findings as file/field/current/proposed/source), `brewdocs.beer` (a full application).
Nothing in the base prompts names any repo — if an overlay only restates the base, delete it.

## 4. The labels

Create them all before the first run — the front door triggers nothing without `@claude`, and a
missing role label makes the stamp hook warn and skip:

`@claude` · `@claude/architect` · `@claude/implementor` · `@claude/designer` ·
`@claude/tester` · `@claude/writer` · `@claude/researcher` · `@claude/security` ·
`@claude/complete` · and the classification set `epic` / `spike` / `bug` / `story` / `task`.

## 5. Ship it

Branch, PR to the target's default branch, maintainer merges. The PR body should say plainly
that nothing can fire until merge and that a drill follows — that sentence is what stops
someone reading silence as failure.

## 6. The maintainer's half — file it, don't do it

Secrets never pass through a session. File an issue on the target listing what to paste into
*Settings → Secrets and variables → Actions*, split by consequence:

- **Required** — `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`; issuing a new one does
  not revoke tokens other repos hold). Without it every routed run fails at its model step in
  seconds; everything scripted still works.
- **Optional, one feature each** — `PROJECTS_TOKEN` (board moves; ⚠️ must be a **classic** PAT
  with `project` + `read:org` — fine-grained tokens cannot reach user-owned Projects v2);
  the dispatch App install plus `DISPATCH_APP_ID`/`DISPATCH_APP_PRIVATE_KEY`, then flip the
  stub's `allowed_bots` (all three or the cascade stays dark); `AWS_TRANSCRIPTS_ROLE`/
  `AWS_TRANSCRIPTS_BUCKET` plus the `AGENT_TRANSCRIPTS` repository **variable** (⚠️ the IAM
  role's OIDC trust policy must also admit the new repo's `sub` claim — the secret alone is
  not enough).

## 7. The drill — what proves it

After merge and the required secret: file a small **real** issue (a genuine question or task —
a synthetic no-op proves routing but wastes the run), and the maintainer applies `@claude`.

Read the result by **jobs, steps, and `num_turns` — never by the tracking comment**, which
looks identical in success and death, and never from `--limit 1`, which happily hands you the
wrong run. Expected anatomy:

- Other label adds (classification at creation, the role stamp) fire sibling runs that skip
  everything — that is the loop guard working, not noise.
- `delegate` green, and the role matching the issue's state (a `spike` routes to the
  Researcher without consulting a model).
- The routed role runs to a real result. If the token is missing it fails env-validation in
  ~3 seconds — that is the boundary behaving, and the drill passes for everything scripted.

⚠️ Two disciplines for every comment you write near a live install: the literal handle (the
`@`-prefixed label name) in any issue or PR comment **starts a run — backticks do not protect
it**; write around it. And re-adding the label is the "run again" gesture, so removing and
re-adding it is never idle cleanup.
