#!/usr/bin/env python3
"""Post-hook for the Researcher. Renders its schema-forced findings onto the spike.

⚠️ THIS EXISTS FOR A SECURITY REASON, not for tidiness. The Researcher is the only role whose
input is arbitrary third-party web content, so it is the only one where a prompt injection has a
plausible author. It therefore holds no shell at all — and without a shell it cannot run `gh`,
so it cannot write its own findings anywhere. This hook is how they reach the issue.

⚠️ REMOVING THE TOKEN FROM THE MODEL STEP DOES NOT WORK, and that was the first fix attempted.
`claude-code-action` re-injects it regardless of what the workflow step declares:

    // src/entrypoints/run.ts
    process.env.GITHUB_TOKEN = githubToken;
    process.env.GH_TOKEN = githubToken;

and `base-action/src/parse-sdk-options.ts` hands the agent `{...process.env}`, so `GH_TOKEN`
and `CLAUDE_CODE_OAUTH_TOKEN` are both readable by anything the agent executes. The credential
cannot be taken away; what can be taken away is the ability to read it. No shell, no read.
(That same file does `delete env.ACTIONS_ID_TOKEN_REQUEST_*`, so OIDC minting is already
closed by the action itself — which is why this job does not need `id-token`.)

APPENDS, never replaces. A spike keeps the maintainer's question; the findings are added below
it. Re-running the Researcher adds another round rather than overwriting the first, because two
passes over a question are a record, not a redraft.
"""

import json
import os

import team

FINDINGS = os.environ.get("FINDINGS", "")
ISSUE = os.environ.get("ISSUE", "")

if not team.REPO:
    team.fail("REPO is required")

if not ISSUE:
    print("Not triggered on an issue — nowhere to post findings.")
    raise SystemExit(0)

if not FINDINGS:
    team.warn(
        f"the Researcher produced no findings for #{ISSUE} — its step failed, or never ran. "
        "The spike is unchanged."
    )
    raise SystemExit(0)

try:
    data = json.loads(FINDINGS)
except json.JSONDecodeError:
    team.warn(f"could not parse the Researcher output for #{ISSUE}; posting it raw.")
    data = None

if data is None:
    body = f"### Findings\n\n```\n{FINDINGS}\n```\n"
else:
    lines = [f"### Findings\n", f"{data.get('answer', '').strip()}\n"]

    options = data.get("options") or []
    if options:
        lines.append("#### Options\n")
        for option in options:
            lines.append(f"**{option.get('option', '').strip()}**")
            lines.append(f"- *What decides it:* {option.get('distinguishes', '').strip()}")
            lines.append(f"- *Costs:* {option.get('costs', '').strip()}\n")

    # ⚠️ verified and inferred are rendered as DIFFERENT THINGS, deliberately. A reader will not
    # re-check a confident claim, so collapsing the two is how an inference becomes a fact.
    evidence = data.get("evidence") or []
    if evidence:
        lines.append("#### Evidence\n")
        lines.append("| | Claim | Source | Checked |")
        lines.append("|---|---|---|---|")
        for item in evidence:
            mark = "✅ read" if item.get("verified") else "⚠️ inferred"
            lines.append(
                f"| {mark} | {item.get('claim', '').strip()} | {item.get('source', '').strip()} "
                f"| {item.get('checkedOn', '').strip()} |"
            )
        lines.append("")

    unknowns = data.get("unknowns") or []
    lines.append("#### Could not determine\n")
    if unknowns:
        for item in unknowns:
            lines.append(f"**{item.get('question', '').strip()}**")
            lines.append(f"- *Why not:* {item.get('whyNot', '').strip()}")
            lines.append(f"- *How to settle it:* {item.get('howToSettle', '').strip()}\n")
    else:
        lines.append("_The Researcher reported nothing outstanding._\n")

    lines.append("#### Recommendation\n")
    lines.append(f"{data.get('recommendation', '').strip()}\n")
    lines.append(
        "> [!NOTE]\n"
        "> Researched from the web and the repository, with no code executed. Any claim above "
        f"marked *inferred* was not read at its source. Nothing is decided by this — #{ISSUE} "
        "stays open until the maintainer chooses, and only then is there a story to shape.\n"
    )
    body = "\n".join(lines)

if team.append_to_comment(
    ISSUE,
    "<!-- claude-team:findings -->",
    body + team.run_footer(),
    "## Research\n\nAppended below the question, which is left as it was asked. Newest last.",
):
    print(f"posted findings on #{ISSUE}")
else:
    team.warn(f"could not post findings on #{ISSUE}")
