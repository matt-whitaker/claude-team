---
name: shape-story
description: File a claude-team story with its tasks in the exact shapes the hooks parse — Branch line, Role stamps, Sequencing contract, sub-issue parenting. Use when shaping backlog work by hand or from a session, in any repo running claude-team.
argument-hint: [what the story delivers]
---

You are doing by hand what the Architect role does in CI, and the hooks cannot tell the
difference — which means the shapes must be exact. `team.branch_line()` and `team.role_stamp()`
are the parsers; when in doubt, verify a body against them rather than against your memory.

## The story

1. Create the story issue first — its number names the branch. Body opens with:

   ```
   **Branch: `<story#>-<kebab-summary>`**
   ```

   Do not create the branch; the first author run's upsert makes the name real.
2. Outcome, boundaries, acceptance criteria — what a careful colleague needs, no more. State
   what is out of scope. An unmeetable criterion is a defect: no issue may require a role to
   spend its whole budget.
3. **Does a specification need writing before the code?** Yes → the story divides and a
   `Role: writer` task is cut first. No → a story one author can finish is stamped as-is:
   `**Role: <role>**` beside its Branch line, no tasks, done here.

## The tasks

Each task's body opens with exactly two lines:

```
**Branch: `<the story's branch>`**
**Role: <implementor|designer|tester|writer>**
```

The Branch line names the *story's* branch — that is what makes it a task. One deliverable per
task; the tester derives from the spec and story, never the implementation.

## Wire it

1. Append the contract to the story body:

   ```
   ### Sequencing
   1. #<first task>
   2. #<next>
   ```

   Numbered lines, one wave per line. Prefer single-task waves — parallel tasks race on shared
   files.
2. **Parent every task to the story via the sub-issues API** — hand-filed issues are never
   auto-parented (`file-sub-issues.py` trusts bot authors only):

   ```
   gh api -X POST repos/<owner>/<repo>/issues/<story#>/sub_issues -F sub_issue_id=<task node id>
   ```

3. Create everything **unlabeled**. The front-door label is the trigger, applied by whoever
   drives — labeling is starting, not filing.

## Verify before handing over

From a claude-team checkout: every task's first lines parse (`team.branch_line`,
`team.role_stamp` — role non-empty, branch equal to the story's), the story's own branch line
leads with its issue number, and the sub-issue count matches the task count. A shape the parsers
reject is invisible to every hook downstream.
