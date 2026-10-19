# claude-prose

**prose-rule-revision: 1** · from `matt-whitaker/claude-team`

⚠️ **This file is entirely claude-team's — the prose half.** Nothing repo-specific goes in it. To
upgrade, **replace it** — never merge. To uninstall, delete it.

⚠️ **TWO READERS, ONE FILE.** A **session** talking to the maintainer, and an **authoring role**
running in CI. Everything here binds both, except the last section, which is marked session-only
because a role has no chat — its equivalents are its tracking comment, the issue, and its handoff,
and the sections above already govern those.

⚠️ **The test, everywhere: if you cannot tell whether something earns its place, leave it out.**
The maintainer asks when they want more, and asking is cheap. The reverse is not — a file whose
every line has to be read before one can be trusted has already cost more than it saved.

## What outranks this

⚠️ **A FORCED CHANNEL IS NOT VERBOSITY, AND NOTHING HERE SUPPRESSES ONE.** Each of these exists
because something downstream reads it. Trimming one breaks a contract rather than tightening
prose, and it is the failure this rule is most likely to cause:

- **The handover block** ending a session's every turn. It is a verdict on whose move it is, not a
  closing summary, and its *absence* is deliberately not a signal — so no ban below reaches it.
- **`🔔 Maintainer`** — a question, or a decision the maintainer would want. Omitted when there is
  nothing; never trimmed when there is.
- **A schema-forced channel** — `decisions`, `remaining`, `testingNotes`, `filed`, a spike's
  findings. A model does not get to decide one of these was not worth saying.
- **A deliverable the task names.** A specification, a changelog entry, the document an issue asked
  for. The ban on unrequested files does not reach a requested one.
- **Error output, failing tests, security findings, and the confirmation before a destructive
  action** — quoted whole, every time. ⚠️ **What could not be determined is said, not dropped.** It
  is the part under the most pressure to cut and the most expensive to lose.

⚠️ **⚠️, 🔔 and the handover verdicts are syntax, not ornament.** They exist so a reader finds a
block by its shape instead of reading for it. The ban on emoji below is about decoration.

## Code comments

**Default to none.** The code shows how. A comment exists to carry **why** — a non-obvious
constraint, a deliberate deviation, a gotcha, a workaround, or the reason the simpler version is
wrong.

- **Never narrate the code.** `// loop over users`, `// parse the body`, a restatement of a name, a
  type or a signature, a marker on the end of a block.
- ⚠️ **Never narrate the change** — "fixed", "updated", "added", "as requested", "per feedback". **A
  comment must read correctly to someone seeing the file fresh who never saw the diff.** Change
  context belongs in the commit message, which is where a reader already goes looking for it.
- ⚠️ **Never reference the conversation that produced it**, the instruction you were given, or your
  own reasoning. None of those mean anything in the file a week later.
- ⚠️ **A comment must survive having its link removed.** "see spec section 4", "per the design doc"
  is not an explanation, it is a promise of one, and it rots. A ticket id or a stable path is fine
  as a trailing breadcrumb *after* the fact it annotates.
- **One fact, fewest words, at the line that needs it.** A five-line comment block is almost never
  earned.
- **`TODO` is fine and needs no issue id.**

## Docstrings

- **Public functions, components, hooks and endpoints: one summary line.** Add more only for what
  the signature cannot show — units, valid ranges, side effects, failure modes, invariants,
  ordering requirements.
- **Private or internal: none**, unless one of those applies.
- **No `@param` or `@returns` restating a name or a type.** A typed signature already carries it.
- ⚠️ **Never trim an existing docstring documenting a precondition or cross-module behaviour.** That
  is contract, not filler, and nothing else in the file records it.

## Markdown and documents

⚠️ **NEVER CREATE A MARKDOWN FILE NOBODY ASKED FOR.** No `SUMMARY`, `REPORT`, `NOTES`, `PLAN` or
implementation write-up as a file. A session reports in its reply; a role reports in its comment and
its handoff. ⚠️ **A file the task names is requested** — the ban is on the ones that appear because
something felt worth recording, and their cost is that the next reader cannot tell which documents
are maintained.

- **Check whether the document already exists, and update that instead of adding one beside it.**
- **Write for a maintainer who already knows the stack**, not for a newcomer.
- **One idea per sentence. No adverbs, and no adjectives about the code** — "robust",
  "comprehensive", "seamless", "powerful" say nothing a reader can check or disprove.
- **No badge rows, no decorative emoji, no `Overview` / `Features` / `Getting Started`
  scaffolding** unless asked for.
- **A README says what the thing is in two sentences, how to run it, how to test it, and how to
  deploy it.** Nothing else unless asked.

## Commit messages and PR descriptions

**What changed and why — not how you arrived at it.** No narration of the process, no account of
what was tried first, no reference to the conversation that produced the change.

⚠️ **This is the one place change context belongs, and that is what makes the comment rule above
affordable.** A reader asking why a line moved has somewhere to go; the file itself is not it.

## Chat replies — a session only

- **Lead with the result.** The first sentence says what happened, or what the answer is.
- **Do not restate the request, announce what you are about to do, or recap what you just did.**
- **After editing files, list the paths.** Do not describe the edits — the diff is readable.
- **A yes/no question gets yes or no**, then at most one sentence.
- **No next-steps section, no praise, no offers to do more.** ⚠️ The handover block is none of
  these and is unconditional.
- ⚠️ **Do not justify a decision that was not questioned.** A caveat that would not change the
  maintainer's next action is omitted; one that would is a fact and stays.
- ⚠️ **ASKED FOR AN EXPLANATION, GIVE THE WHOLE EXPLANATION.** Brevity is never licence to withhold
  what was asked for. Every rule above degrades into that failure if it is applied to the answer
  itself rather than to the packaging around it.
