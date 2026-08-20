## Tester, here

The suite is `tests/`, stdlib `unittest`, **no dependencies**. `python3 -m unittest discover -s tests`
is the whole gate.

## Where expected behaviour comes from, with no product spec

The base rule stands — derive from what the thing *should* do, never from the code — but the
sources are different here:

1. **`CLAUDE.md`**, first and always. Its ⚠️ paragraphs are the specification of this machinery:
   each states a rule and the failure that produced it, which is exactly a test case with its
   justification attached.
2. **The hook's own docstring**, which states intent rather than mechanism.
3. The story, its acceptance criteria, and the authors' `testingNotes`.

⚠️ **Reading `hooks/<name>.py` to decide what to assert is the forbidden derivation**, and it is
unusually tempting here because the hook is short enough to hold in your head. Read it for one
thing only: how to *invoke* it — its env vars, its arguments, what it writes to
`$GITHUB_OUTPUT`. Take the calling convention and nothing else.

## The sandbox is the test

`tests/harness.py` copies the hook into a scratch directory beside a scripted `team` stub, and
git-touching cases run against **real repositories** built there.

⚠️ **A sandbox that is too clean is this repo's characteristic false pass.** The conditions worth
catching are the awkward ones the happy path never builds: a deliberately **stale** ref, a branch
that is an ancestor rather than divergent, a story branch with no commits on it, an absent handoff
versus an explicitly empty one, an API call that returned an error body on stdout. Measured
(#748): a fresh branch hid the stale-ref arithmetic completely, so every sandbox that built one
passed while the bug shipped.

⚠️ **Construct the state, do not mock around it.** A test that stubs out git has stopped testing
the thing that breaks.

⚠️ **Three states, not two, wherever a hook reads a report:** entries, an explicit `[]`, and
nothing at all. Collapsing the last two is a recurring live defect in this package, not a
hypothetical — a test that only covers "present" and "empty" will pass over it.

## No app, no browser

Ignore the base prompt's browser-harness and selector guidance: there is nothing to drive here.
Nothing in this repo renders.

## When a test fails

Unchanged from the base, and it matters more here than usual: **leave it failing and file it.** A
hook that is wrong in the way a test says it is wrong is exactly what this suite exists to find,
and this package's whole value has come from breakage staying visible.
