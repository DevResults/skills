# dr-code-review

Thorough code review for DevResults pull requests. It covers ordinary
correctness briefly and spends its depth on the things a generic reviewer
cannot know: instance isolation, the permission layers, pseudonyms and the
localization pipeline, the minifier, and what generates support tickets.

Run it from inside the DevResults app repo, not this one.

## Usage

```
/dr-code-review
```

It detects what to review — the PR for the current branch, the branch against
its base, or a PR number you name. Two opt-in flags, neither on by default:

- `--fix-first` — apply mechanical fixes before triage
- `--full` — re-review the whole diff after fixes, not just the fix commits

## How it runs

The review is read-only: **it changes no code by default.** Findings go to a
tracking file in the repo under review — `.reviews/PR-<number>.md`, or
`.reviews/<branch>.md` when the branch has no PR — excluded locally via
`.git/info/exclude` so it never lands in a commit.

It then offers two phases against that file, each opt-in:

1. **Triage** — walk the findings and decide each one.
2. **Remediation** — apply the accepted fixes and re-review them.

Both are resumable across sessions. The tracking file is the only state, so
you can decline triage, come back later, and pick up where you left off.

## Source of truth

`SKILL.md` is the skill. This file exists to orient anyone browsing the folder
on GitHub. For what the review actually checks, read `SKILL.md` and the files
it routes to in `references/`.
