---
name: dr-code-review
description: Thorough code review for DevResults PRs, encoding the institutional knowledge that engineering and support reviewers bring. Use when reviewing a branch or PR in the DevResults repo.
user-invocable: true
---

# DevResults Code Review

This is the full review for DevResults work — it does not assume another
reviewer ran first. It covers ordinary correctness briefly and spends its
depth on the things a generic reviewer cannot know: instance isolation,
the permission layers, pseudonyms, the minifier, and what generates
support tickets.

It reviews both human- and agent-authored code. The agent-smells pass runs
either way.

## 1. Select the input

Detect, don't ask:

- If a PR exists for the current branch
  (`gh pr view --json number,title,body,baseRefName`), review the PR. Read its
  description and its filled-in checklist — a submitter who ticked "All strings
  are localized" on a diff full of bare literals is itself a finding.
- Otherwise review the branch against `main` (`git diff origin/main...HEAD`).
- If the user names a PR number or URL, use that.

**Diff against `baseRefName`, not `main`.** PRs here are routinely stacked.
`git diff main...HEAD` on a stacked PR pulls in the whole base PR and inflates
the surface — a 16-file review becomes 26. Get the base from
`gh pr view --json baseRefName`, then:

```bash
BASE=$(gh pr view --json baseRefName -q .baseRefName)
git fetch origin "$BASE"
git diff "origin/$BASE...HEAD"
```

Fetch and diff `origin/<base>`, not the bare ref. The base of a stacked PR is
usually someone else's branch and has no local ref in the reviewer's clone —
`git diff <base>...HEAD` then dies with "unknown revision" before the review
starts, and the obvious recovery is to fall back to `main`, which is the exact
inflation this section exists to prevent.

When the base is not `main`:

- Say so at the top of the output, with both file counts.
- Findings that belong to the base PR go in a short **Out of scope — belongs to
  #NNNN** list. Name them; do not drop them silently and do not file them here.
- Ask what happens to data written while the base PR is deployed *alone*. A
  second PR that changes the meaning of a column the first one populates leaves
  rows in an intermediate state that no code path re-examines. Either the two
  must ship together, or someone has to clean up — that is a human-verification
  action with a concrete query in it, not a caveat.

Read the whole diff before consulting any reference file.

### Modes

Two opt-in flags, detected from the user's request in flags or in words:

| Flag | In words | Effect |
|---|---|---|
| `--fix-first` | "do a first pass", "fix the obvious ones first" | Apply mechanical fixes before triage. [references/triage.md](references/triage.md). |
| `--full` | "full re-review" | Re-review the whole diff instead of just the fix commits. §9. |

Neither is the default. Absent both, the review changes no code and re-reviews
only what the fixes touched.

`references/triage.md` owns the `--fix-first` rules in full — what may and may
never be auto-fixed, the preconditions checked before the first edit, and the
one-commit-per-auto-fix rule that per-row `Revert` depends on. Read it before
applying anything under that flag; §9 is remediation the human already agreed
to, and its commit-grouping rule does not apply to the first pass.

## 2. One hop out

Most of the value in this review is outside the diff. The PR template asks
reviewers to test "for broader potential regressions than actual code changes
might suggest" — this is how you do that mechanically. For each symbol the
diff changes:

1. Find its other callers and references.
2. For each new or changed entity/field, walk `references/surfaces.md`.
3. For each changed permission check, find the other validators in the same family.

**Stop at one hop.** Do not chase transitively. Anything beyond one hop —
client-authored custom queries, dynamic tables, real client data — goes in
the Human verification section (§7), not into more searching.

### The PR description is part of the diff

Every factual claim in the PR body is a check, not context. Verify them the
same way — one hop, cite the line:

- "This is a no-op today because nothing overrides X" — find the overrides.
- "The old catch was swallowing genuine `Languages` failures" — read what the
  old catch actually wrapped. If it only ever wrapped one property access, the
  claim is wrong and that is a finding against the description.
- "No truncation risk" — check the attribute against the table definition
  against the source column.

Report both directions: claims that overstate what the change does, and
user-visible consequences the body omits. Say which claims held up — a
description that survives checking is worth stating, because it tells the next
reader the body can be trusted.

## 3. Generic pass (inline — keep it short)

The model does not need to be taught what these are, only reminded to look.
Spend a few minutes, report anything real, and move on:

- Obvious correctness: null/undefined paths, off-by-one, inverted conditions,
  swallowed exceptions, unawaited async.
- Error handling: what happens on the failure branch, and what the user sees.
- Injection and unsafe input: raw SQL string concatenation, unescaped HTML.
- Secrets: keys, connection strings, GemBox license keys (these belong in
  `SecureSettings.config`, never committed).
- Test coverage: are there tests, do they test the requirement rather than the
  implementation, do they cover the negative path.
- Dead code, unused imports, leftover debug output.

Depth lives in the reference files below, not here.

## 4. Route to the reference files

Read the reference file when its trigger fires. Note in the coverage footer
(§7) which ones you skipped and why.

| Trigger in the diff | Read |
|---|---|
| Any query, repository, `DbSchema.xml`, `AbstractTableCompiler`, raw SQL, schema change | [references/data-layer.md](references/data-layer.md) |
| `DevResults.Core/Security/`, `[AuthorizedRoles]`, any validator, role or feature-flag check, a new endpoint | [references/permissions.md](references/permissions.md) |
| A new or changed entity, field, or domain concept | [references/surfaces.md](references/surfaces.md) |
| Any user-facing text, label, message, or template — **and any occurrence at all of `__(`, `__html(`, `\| __`, `GetString`, or `GetFormattedString`, whatever it is applied to** | [references/localization.md](references/localization.md) |
| Frontend code, a new AngularJS registration, `vite.config.ts`, a new dependency | [references/bundle.md](references/bundle.md) |
| New files, or new code added to Web Forms / `ng/` / `src/` | [references/placement.md](references/placement.md) |
| Always | [references/agent-smells.md](references/agent-smells.md) |
| Always | [references/support.md](references/support.md) |

Reference files carry a `last-verified` date. **Confirm any file path or symbol
they cite still exists before relying on it.** If one is wrong, say so in the
review — a stale reference file is worse than none, because it gets trusted.

## 5. The five hard gates

These are Blockers. A diff that trips one is not approvable until it is
addressed or explicitly justified in the review.

1. **Server-side enforcement.** A UI affordance gated on a permission must have
   a named server-side check. Cite the line, or report its absence.
   See `references/permissions.md`.
2. **Instance scoping.** A query over an `IInstancedContentObject` with no
   `InstanceID` predicate is a candidate cross-tenant leak. See
   `references/data-layer.md`.
3. **Removed or renamed table/column.** Clients write their own custom queries
   against the schema. No compiler catches this. See `references/data-layer.md`.
4. **PII in exceptions or logs.** Contact names, emails, result values, document
   contents. See `references/support.md`.
5. **Client content through the localization pipeline.** `__()`, `__html()`, and
   the `| __` filter register whatever they are handed into `dbo.LanguageStrings`
   and the scheduled worker sends it to Google Translate. A bound expression
   piped through `| __` — `{{item.title|__}}` — is a candidate third-party data
   disclosure, not a translation nit. See `references/localization.md`.

State in the coverage footer when a gate has no surface in the diff. "No new
queries" is a result; silence is not.

## 6. Build it and run the tests

Do this yourself. A review that only reads is a review that can be confidently
wrong about whether the branch even compiles, and it leaves you no baseline if
you later remediate.

- Build the projects the diff touches — `just msbuild <project>`.
- Run the test assemblies covering them — `just vstest <assembly>.dll`.
- Report a command/result table with real numbers: total, passed, skipped, and
  any pre-existing warnings you did not introduce.

Skip only when the diff is docs-only, and say so. If you cannot run them —
missing tooling, a build that fails for reasons predating the branch — report
that explicitly. An unrun suite is not a clean one, and reporting it as clean
is the worst outcome available here.

## 7. Output

Write the review to a tracking file and tell the user the path. Anything past a
handful of findings is unreadable as chat, and triage and remediation need
something to record outcomes against.

**The schema is not optional.** Read
[references/tracking-file.md](references/tracking-file.md) and follow it exactly
— path, local exclusion, ID rules, anchor rules, tag set, column order. Every
later session reads this file and nothing else, so a file that drifts from the
schema is a file the next session cannot resume.

Open with the scope (base ref, file count, head sha), the run log line, the
verdict counts, and the §6 verification table.

### Findings

Lead with the summary table, then the `<details>` body per finding, then the
by-file index. **Every finding cites a `file:line` and the anchored line's text,
or it does not get reported.** A page of plausible generalities is the failure
mode for a review this size; the anchor requirement kills it.

Each finding carries:

- **ID** — `DR-NNN`, assigned in report order, never renumbered.
- **Severity** — `Blocker` (the five gates), `Should fix` (real defect, doesn't
  block), `Consider` (nits, refactors, missed refactoring opportunities).
- **Confidence** — `Verified` (you read the code and confirmed it) or
  `Candidate` (pattern match, needs a human to confirm). Much of this skill is
  heuristic; say which is which. Do not report a Candidate as Verified.
- **Tag** — one value from the closed set in `references/tracking-file.md`.
- What is wrong, and why it matters — in that order, in one or two sentences.
- **Proposed disposition** — what you would do with it: `Fix` (with the patch),
  `Defer`, `Won't fix`, `Withdraw`, or `Discuss`. This is a proposal, not an
  action. **A read-only review changes no code.** Triage (§8) is where a human
  accepts or overrides it.

**Write the proposal into the `Proposed` field of the finding's `<details>` body,
and leave the `Disposition` column empty.** A review never fills
`Disposition` — that column is triage's, and an empty cell is the only signal a
later session has that the row has not been decided yet. Filling it with your own
proposal makes the next session read your recommendation as a human decision and
apply it. New findings are written `Disposition` empty, `Outcome: Open`; see
`references/tracking-file.md`.

**`Verified` means the premise was checked, not just the line.** Before filing
any finding of the form *"this violates the convention here"* — alphabetical
ordering, file layout, a naming pattern, "everything else in this file does X" —
read enough of the surrounding code to confirm the convention actually holds.
An ItemGroup that looks alphabetical for six lines may not be alphabetical at
all, and a finding whose premise is invented is worse than a missed one: it
costs the author time and it discredits the rest of the review. If the
convention doesn't hold, there is no correct position to move the new line to,
and there is no finding.

If a finding is withdrawn after filing, keep it in the file marked
**Withdrawn**, with what the premise was and why it was wrong. Deleting it hides
the correction from anyone who already read the review.

### Human verification required

Concrete actions, not caveats. This is where the things you cannot check go:
client custom queries, dynamic tables, real client data, running the app.

Each gets an `HV-NNN` id and an owner drawn from the PR template's three roles
(`Submitter`, `Data Reviewer`, `Engineer Reviewer`), so triage can walk them and
so an unfinished one is visible in the close-out instead of buried in prose.

Write `HV-` rows with the `Disposition` cell **empty**, not `Open` — same rule as
the findings table. `Open` means a human was asked and chose to leave it open;
empty means nobody has been asked yet, which is what triage looks for when it
resumes. See `references/tracking-file.md`.

Write instructions, not warnings:

> - HV-001 · Data Reviewer · Search client custom queries for
>   `Activity.StatusCode` — this PR renames it.
> - HV-002 · Engineer Reviewer · Run `just build-client` and load the app
>   minified; this adds an AngularJS service whose DI annotation is implicit.
> - HV-003 · Engineer Reviewer · Log in as a Partner user and confirm the new
>   tab is hidden **and** the endpoint 403s.

An empty findings list plus an empty verification section means something went
wrong with the review. Both being empty is a signal, not a pass.

### Coverage footer

A table — dimension, whether you looked, and the result ("no permission surface
in this diff"). Silence otherwise reads as clean when it may mean you didn't
look.

### PR template checklist

The repo's `.github/pull_request_template.md` has Submitter, Data Reviewer, and
Engineer Reviewer sections. Address every item somewhere in the review — as a
finding, as an `HV-` action, or in the coverage footer. Do not restate the
checklist with ticks; the reference files are the deepened version of those
lines.

### Then offer triage

Report the path and the verdict line, then **offer** to start triage — do not
start it unprompted. Declining is normal: the file is resumable and triage can
be invoked later against it with no re-review. See §8.

## 8. Triage — only when asked

A review does not decide anything on its own. When the human accepts the offer
from §7, read [references/triage.md](references/triage.md) and follow it.

Triage also runs standalone against an existing tracking file, with no
re-review. `references/triage.md` owns how to resume; do not restate it here.

Keep this section a pointer. The wizard's mechanics — dispositions, pacing,
resume rules — belong to `references/triage.md`, and a second copy here is a
second thing to keep in sync.

## 9. Remediation — only when asked

A review does not change code. If the user asks you to fix what you found:

- **One commit per coherent group of findings**, with a message that says what
  the code now does — not "address review feedback." Comment-only fixes group
  together fine; a behavior change does not group with anything. This rule is
  for remediation the human already agreed to; the `--fix-first` first pass is
  explicitly exempt and commits one auto-fix per commit, per
  `references/triage.md`.
- **Re-run §6 after each commit** and confirm you are back to the baseline
  numbers, not merely green. If §6 was skipped at review time because the diff
  was docs-only, there are no baseline numbers: confirm instead that the fix
  commits are still docs-only. The moment a fix touches code, §6 applies — build
  and test what it touched, and record that as the baseline in the tracking file,
  noting it was established at the fix rather than at the review.
- **No speculative fixes.** If you could not demonstrate the failure, do not
  change the code for it. Broadening a `catch` against an exception you never
  showed reaches that line trades a known behavior for an unknown one. Leave it
  as an open finding and say in the output that the fix was considered and
  rejected, with the reason.
- **A test finding is only closed by a discriminating test.** See
  `references/agent-smells.md` §7 — revert the fix, capture the failure output,
  restore, and put that output in the review. A new test that passes both
  before and after closes nothing.
- **Update the findings table.** Every row ends with one value from the closed
  `Outcome` set in `references/tracking-file.md` — no other value is valid — and
  open rows get an owner action.
- **Re-review after the fixes land.** They are new code. `references/triage.md`
  has the rules: fix-commit diff by default, whole diff under `--full`, new
  findings prefixing their `Summary` with `from-fix DR-NNN`, and a two-cycle cap
  counted from the run-log lines in the tracking file.
- **Close a row only on evidence.** The anchored line's text must have changed
  and §6 must be back to baseline. A fix that was claimed but not made is
  `Needs recheck`, not `Fixed`.
- **Close out with the counts line and the handoff** — open findings with owners,
  plus the outstanding `HV-` items.

## Related project skills

The DevResults repo has its own skills that define the sanctioned way to build
things: `database-schema`, `creating-api-endpoints`, `angularjs`,
`planning-implementation`, `package-json-changes`, `setup-check`. If one covers
what the diff is doing, the diff should match it — cite the skill in the
finding. This makes those skills self-enforcing.
