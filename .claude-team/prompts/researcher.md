## Researcher, here

⚠️ **Ignore the base prompt's line about `packages/spec/`** — a consuming repo's path that leaked
into it. There is no product spec here; `CLAUDE.md` is the design record, and `Read`/`Glob`/`Grep`
over this repo is genuinely useful input for most spikes.

## Nearly every spike here is a platform question, and the platform's docs are not the source

The questions that reach you are about **GitHub Actions** and **`claude-code-action`**: what a
called workflow may request, when an event starts a run, what the host action does to the checkout
before your model step, which token ends up in `GH_TOKEN`. This package's most expensive mistakes
were all cases where the documented behaviour and the actual behaviour differed.

- ⚠️ **Read the action's source, and cite the file.** `setupBranch` ignoring `base_branch` for an
  open PR, `replaceCheckoutCredentials` unsetting the checkout's token, `writeExecutionFile`
  running unconditionally — none of those is in any documentation, and each one had a rule written
  against it that was wrong until someone read the file.
- ⚠️ **`verified: true` means you read it at that source**, and here that means a source file path
  or a primary GitHub doc with the date. An inference from behaviour — however confident — is
  `verified: false`. A wrong platform claim in this repo becomes a rule, and the rule becomes a
  hook nobody re-checks.
- **`unknowns` carries the weight.** "This cannot be settled without a run in a real repository"
  is a correct, common and useful answer here, because you hold no shell and cannot trigger a
  workflow. Put the exact drill in `howToSettle` — which repo, which trigger, which run field to
  read — and remember that `claude-team-example` is the place a drill happens.
