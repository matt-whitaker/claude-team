# ONBOARDING — installing the team into a repo

This is a runbook for a Claude session. Point one here together with a **target repo** and it
should produce a working install without further research. It is the sequence that onboarded
`brewdocs.beer-kb`, written down. Everything ships branch → PR — never push the target's
default branch — and the proof of the install is post-merge, because `issues` events always run
the workflow from the default branch.

Private targets are supported (since `v1.1`). Public and private differ in nothing below.

⚠️ **If the target is ALREADY INSTALLED, go to §0 and do not run §1–§7.** They create things that
exist, and §3 in particular would overwrite an overlay carrying the repo's whole personality.

## 0. Already installed? Upgrade instead

⚠️ **THIS FILE INSTALLED AND NEVER RE-INSTALLED, AND THAT IS HOW A FLEET DRIFTS.** Every step
below §0 is written for a fresh target. A session pointed at an installed repo had no instruction
for the case it was actually in, so the consumer half of an upgrade was never stated anywhere and
"upgrade" meant *bump the ref and hope*.

**Detect the case first.** The target has `.github/workflows/claude.yml` calling this workflow.
Read its `uses:` ref — that is the installed version. There is no second version number to invent:
the pin *is* the signal.

```bash
grep -o 'team\.yml@[^ ]*' <target>/.github/workflows/claude.yml   # installed
git ls-remote --tags https://github.com/matt-whitaker/claude-team  # available
```

Then, in order:

1. **Read [`CHANGELOG.md`](CHANGELOG.md) from the installed ref to the current tag.** Every version
   heading carries an `**Action required:**` line. If they all say `no`, steps 2 and 5 are the
   whole upgrade.

2. **Bump the `uses:` ref, and the rule's `team-ref` with it.** That ref is the
   only pin a consumer holds — `TEAM_REF` lives inside the workflow and moves with the tag, so a
   consumer never edits it and must never be told to. ⚠️ **Re-fetch `.claude/rules/claude-team.md` from the
   new ref** (§2) and check its `team-ref` matches: the two are one fact in two places, and a
   mismatch is exactly the half-done upgrade nothing else can see. ⚠️ A repo that deliberately
   tracks `@mainline` skips the bump; see the release note in `CLAUDE.md` for which ones and why.

3. **Reconcile the stub — do not recreate it.** Diff it against
   [`templates/consumer-stub.yml`](templates/consumer-stub.yml). Everything but the header comment,
   the `uses:` ref and the `with:` values should be identical, so the diff is a real check rather
   than noise. **New inputs appear here and nowhere else**: a consumer's stub is frozen, so a new
   input never arrives on its own — it shows up as a line present in the template and absent in the
   target.

4. **Leave the overlays alone unless the CHANGELOG says otherwise.** They are the repo's
   personality and this file has no business rewriting them.
   ⚠️ **The exception that has already bitten: a base-prompt rule that an overlay now contradicts.**
   An overlay composes *after* the base, so it **wins** — which means a base change tightening what
   a role may do reaches nothing if the overlay still grants it. When an entry says a role's scope
   narrowed, grep the overlays for the old grant.

5. **Re-run everything the pin cannot carry — unconditionally, every time.** It is idempotent and
   cheap, and this is the half a version number can never express:
   - **§4's label loop.** ⚠️ Labels live in GitHub, not in the clone, so no ref bump has ever
     touched them. It is the one step already written to be idempotent and it still drifted,
     because nothing told anyone to re-run it.
   - **The board** — is `project_number` still the board this repo's work goes on?
   - **§6's settings and secrets** — has the CHANGELOG added a required one? *Allow GitHub Actions
     to create and approve pull requests* is the one that fails late and looks like an engine bug.

6. **Drill again (§7) only if something structural moved** — a new input, a routing change, a
   changed role set. A pure prose release does not earn a run.

⚠️ **Ship it the same way as an install: branch → PR → merge.** Never push the target's default
branch, and remember nothing takes effect until merge, because `issues` events always run the
workflow from the default branch.

## 1. Decide the inputs

Settle these before touching files; each is a judgment call about the target, not boilerplate.
⚠️ **Two of them are answers only the maintainer holds** — the board (`project_owner` /
`project_number`) and the dispatch App's slug. They are not derivable from the target repo:
**ask, and do not proceed on a guess.** Every other input you can settle by reading the repo.

- **`project_owner` / `project_number`** — the GitHub Projects board its issues and PRs go on.
- **`allowed_bots`** — **ask the maintainer for the dispatch App's current slug**, the same way
  you ask for the board. Two questions, asked outright: *should the cascade drive this repo*,
  and *what is the App named right now*. ⚠️ Ask for the name even if you think you know it —
  Apps get renamed, the slug is the identity, and a stub admitting a stale slug refuses every
  cascaded run at setup with *"Workflow initiated by non-human actor"*. The answer `""` is the
  explicit decision to start **dark**: a finished task will not dispatch the next one, and the
  maintainer's label gesture drives everything — a valid starting state, since the cascade is an
  upgrade, not a prerequisite. ⚠️ The slug only *admits* the App: the cascade also needs the App
  installed on the repository and its secrets set (step 6). ⚠️ Name the App, never `*`: a
  wildcard admits any App on GitHub.
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

### The rule, written in this same step

A consumer's clone holds the stub and the overlays, and neither tells a **session** opened against
that repo what the team is. Install the rule that does, from the same tag you just pinned:

```bash
mkdir -p <target>/.claude/rules
curl -fsSL https://raw.githubusercontent.com/matt-whitaker/claude-team/vN/rules/claude-team.md \
  -o <target>/.claude/rules/claude-team.md
```

⚠️ **Set its `team-ref` to the ref you pinned above.** It is not a second version number — it is
the pin, recorded where a session reads rather than where a workflow does, and it is why the two
are written in one step. ⚠️ **A `team-ref` that disagrees with the `uses:` pin is a half-done
upgrade**, and the only part of one a clone can detect on its own.

⚠️ **It carries no role instruction.** A role is given `prompts/` at run time; a rule scopes by
file path, never by who is running.

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
