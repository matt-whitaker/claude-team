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
  is `npm run <anything>` wants it even with zero dependencies. ⚠️ `true` requires a
  **committed `package-lock.json`**, even with zero dependencies: `actions/setup-node`'s npm
  cache fails the author job at setup without one — *"Dependencies lock file is not found"*, a
  message that reads like a caching detail but means the repo lacks a lockfile — and `npm ci`
  two steps later requires it anyway. A spike passing proves nothing here: the Researcher
  builds nothing, so the first *author* run is where this surfaces.
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
missing role label makes the stamp hook warn and skip.

[`templates/labels.json`](templates/labels.json) is the canonical set: fourteen labels with their
colours and descriptions. Apply it rather than typing them, so a fleet reads the same way at a
glance — the colour is doing real work on a board, where `@claude/security` in red and
`@claude/complete` in green are how you find a run's state without opening anything:

```bash
curl -s https://raw.githubusercontent.com/matt-whitaker/claude-team/mainline/templates/labels.json \
  | jq -c '.[]' | while read -r l; do
      name=$(jq -r .name <<<"$l"); color=$(jq -r .color <<<"$l"); desc=$(jq -r .description <<<"$l")
      gh label create "$name" -R <owner>/<repo> --color "$color" --description "$desc" 2>/dev/null \
        || gh label edit "$name" -R <owner>/<repo> --color "$color" --description "$desc"
    done
```

⚠️ **The `create || edit` pair is deliberate** — it is idempotent, so it both seeds a new consumer
and re-syncs one whose colours have drifted. brewdocs.beer-kb was onboarded by hand before this
file existed and ended up with every role the same purple, which is exactly the failure this
removes.

A repo may add labels of its own; nothing here removes them.

## 5. Ship it

Branch, PR to the target's default branch, maintainer merges. The PR body should say plainly
that nothing can fire until merge and that a drill follows — that sentence is what stops
someone reading silence as failure.

## 6. The maintainer's half — file it, don't do it

Secrets never pass through a session, and neither do repository settings. File an issue on the
target listing what the maintainer has to set by hand, split by consequence.

### Secrets — *Settings → Secrets and variables → Actions*

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

⚠️ **Link the README's *Inputs and secrets* table in that issue rather than restating it.** It
carries what each item buys, what breaks without it, and where to obtain it — and the three that
need more than a secret pasted. Two copies of this list is how they drift, and the copy a
maintainer follows is the one that has to be right.

### Settings — *Settings → Actions → General*

⚠️ **"Allow GitHub Actions to create and approve pull requests" must be ON**, or a story's PR is
never opened. `open-story-pr.py` runs with `secrets.GITHUB_TOKEN`, and with that box unchecked
GitHub refuses the create whatever the `permissions:` block says — so the `pull-requests: write`
the stub already grants is neither sufficient nor the thing to check when this fails.

⚠️ **It fails late, and it fails looking like an engine bug.** Nothing exercises the story-PR
path until the first story finishes its *last* task, which can be days after the drill below has
passed. It then surfaces as a red `Open the story's PR when the last task lands` step reading
*"could not open the story PR — open it by hand"*, with the story's work sitting unmerged on a
branch nobody is watching. On the consumer that found it, three stories needed their PRs opened
by hand first, and the cause took a differential against a working install to locate.

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

⚠️ **The drill stops here, and the install does not.** Routing and one role are all it proves.
The cascade, the story PR and the create-PR setting above are first exercised when a real story
finishes its last task — so treat that first completed story as the second half of the drill,
and read its final run's steps the same way.

⚠️ Two disciplines for every comment you write near a live install: the literal handle (the
`@`-prefixed label name) in any issue or PR comment **starts a run — backticks do not protect
it**; write around it. And re-adding the label is the "run again" gesture, so removing and
re-adding it is never idle cleanup.
