---
name: explain-pr
description: "Explains a GitHub pull request to a reviewer who will not read the code, as one Markdown comment ready to post on the PR: what it does for each actor, where the change lives and how it flows, its side effects and whether each one can be undone, whether it agrees with the ticket and the design, the decisions nobody approved, whether the tests prove it, and who finds out if it breaks. Use when someone wants to understand, judge or approve a PR without reading the diff, asks to make a PR easier to review, wants a reviewer-facing summary, diagram or risk read of a PR, or says they won't read the code. Works on any repository and stack. Never posts without the user's yes."
disable-model-invocation: false
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Explain a PR to a reviewer who will not read the code

The reader will approve or reject this PR from your comment alone. They answer five questions with it:

1. What does it do?
2. How does it do it?
3. Does it agree with what was decided?
4. Do the tests prove it?
5. What happens if it is wrong?

They cannot catch a mistake in your comment by reading the code. So the one rule above all others: **every claim comes from a source they can check, or it is marked as an inference.**

## 1. Gather

Read everything before you write anything.

- **The PR:** `gh pr view <n> -R <owner/repo> --json title,body,headRefName,files,additions,deletions,commits` and `gh pr diff <n> -R <owner/repo>`.
- **The ticket:** find the linked issue or ticket in the PR body, the title or the branch, in whatever tracker the team uses (GitHub Issues, Jira, Linear…). Read its description and acceptance criteria with that tracker's CLI or MCP (for example `gh issue view <n>` or `acli jira workitem view <KEY> --fields summary,description,status`). Follow its links to an epic spec or a design doc when the ticket says the spec lives there.
- **Design docs:** any document the PR body or the ticket links, and any design file the PR itself touches.
- **The code around the diff, at the PR head.** A diff hides the shared path it plugs into: a base class, a concern, a caller, a shared service. Read those files at the head, without touching the user's working tree:
  - with a local clone: `git -C <clone> fetch -q origin pull/<n>/head` then `git -C <clone> show FETCH_HEAD:<path>`;
  - without one: `gh api "repos/<owner>/<repo>/contents/<path>?ref=<headRefName>" -H "Accept: application/vnd.github.raw"`.
- **What runs on merge.** List the CI workflows whose triggers match the changed paths on the default branch (`.github/workflows/*`, `Jenkinsfile`, `atlantis.yaml`). A workflow that pushes, deploys, publishes or syncs is a side effect of the PR even though the diff does not show it.
- **The tests' bodies, not only their names.** A test named "when the request expires" that never makes anything expire proves nothing about expiry.

When the tests do not check something the reader needs, check it yourself once (a script that compares the copy with the ticket, a count of a term across a file) and say so in the comment: "checked by hand for this review". Do not run the change itself.

## 2. Write the comment

Write one Markdown comment in the PR's language. Follow `references/comment-template.md` for the exact shape. The sections always keep their numbers, so a reader who has seen one comment can find their way in the next.

### Header

- **Risk: low / medium / high.** One or two sentences: why, and the single main risk, pointing at the section that shows it. No score, no weights, no number.
- **Size:** production files and lines against test files. Say "No logic" when only data or copy changes.

### 1. What changes for each actor

The actor is whoever meets the change: an end user, an internal operator or admin, a developer running a command, an API client, a scheduled job, a downstream team. Show what each one sees, one scenario per row, with the real values from the tests or the ticket (amounts, error codes, messages, dates). Pick the form that fits the surface:

| Surface | Show |
|---|---|
| API or mutation | request situation → result or error code |
| Callback, job or event | incoming state → what the system books, sends or changes |
| CLI or script | the terminal output per situation |
| UI or copy | the text as the screen will show it: one row per part of the screen, one column per screen state (example: empty, loaded and error); other languages in a collapsed block |
| Infrastructure | what is created, changed or destroyed, per environment |

Add one line on what happened before this PR when the behaviour changes.

### 2. How it works

- **Where the change lives:** a Mermaid `flowchart` of the components it touches (packs, layers, services, apps, external systems, data stores), with what changed inside each and the arrows between them. When the repository names its own layers or packs (for example domain, ports, adapters, app, cli), the subgraphs are those layers, so the reader sees which layer each change sits in. End with one sentence on boundaries: does it respect the pack, layer or service boundaries, or does it cross one?
- **The flow:** a Mermaid `sequenceDiagram` when something happens at runtime. Leave it out when nothing runs (copy, constants, docs).
- **The flow diff:** when the PR changes a flow that already exists, a `diff` block of the steps before and after. It shows the reader only what changed.

Every name in a diagram is an actor, a system, a component or a data store. **Never a file, class, method or function name.** Name a data store by what it holds ("runner config", "account events"), not by its file name, path or table name. Choose the smallest set of diagrams that makes the point.

### 3. Side effects

A table: each thing the change writes, sends, charges, deletes, publishes or deploys, and whether it can be undone. Mark the one-way doors in bold: money moved, a message or push sent, data deleted or migrated, a release that cannot be recalled. Include the effects of CI on merge. When a plain revert is unsafe (pending records of a deleted type, a migration, a flag that must go off first), say in which order to roll back.

### 4. Comparison with the sources

A table of each acceptance criterion, then each decision in a design doc that applies: ✅ done, ⚠️ done in a different way or only partly, ❌ not done, each with its evidence. Name the test or the check that proves each row. Then one sentence: does the PR description agree with the change?

### 5. Decisions that no source approved

Choices the code made that the ticket, the design and the PR description do not cover, numbered, each phrased so the reader can answer yes or no. Include behaviour the PR inherits from an existing path when it matters more for this case than for the original one. Leave out choices nobody would argue about. This section is the one only the reader can answer, so make it short and sharp.

### 6. Do the tests prove it?

A table: each scenario from section 1 and each criterion from section 4 against the test that proves it. Mark ❌ for a gap, and for a test whose body does not prove what its name claims. Mark checks you did yourself as "checked by hand for this review".

### 7. If it breaks in production, who finds out?

A table of each way it can fail and the signal that reports it: an alert, a metric, a log, the user seeing an error, or nothing. Point out in bold a failure that loses or holds money or data with no alert. When nothing runs, say so in one sentence and say who would notice a mistake.

### Sources

A collapsed `<details>` block that lists the ticket, the docs, the test files and the code files each claim came from. **File paths appear here and nowhere else.**

## 3. Writing rules

- The reader reads the comment in about ten minutes: keep the open text under about 1,500 words. When a table has more than about ten rows, keep the rows that carry a finding open and put the full table in a collapsed `<details>` block under it.
- Plain words and short sentences. Explain a domain term the first time: follow it with a few words in parentheses that say what it is.
- An inference has the words *Inference, not tested:* in front of it.
- Never write what the code "probably" does. Read it, or mark it as an inference.
- A section with nothing to say keeps its heading and one sentence that says why.
- Mermaid must render on GitHub: put labels with spaces or symbols in quotes, use `<br/>` for line breaks, and keep parentheses out of node ids.

## 4. Deliver

1. Write the comment to `pr-<n>-explained.md` in the session's scratchpad directory, or in the current directory if there is none.
2. Give the user the path, the risk line, and the questions from section 5.
3. Post it only when the user says yes: `gh pr comment <n> -R <owner/repo> --body-file <path>`. Never post it on your own.
