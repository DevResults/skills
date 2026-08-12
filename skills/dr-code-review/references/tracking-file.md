<!-- last-verified: 2026-08-07 -->

# The tracking file

Every review writes one. It is the only state store for triage and remediation —
no sidecar, no database, no carryover between sessions. If it is not in this
file, it did not happen.

## Location

`.reviews/PR-<number>.md` at the root of the repo under review, or
`.reviews/<branch>.md` when the review has no PR.

Exclude the directory locally before writing:

```bash
EXCLUDE=$(git rev-parse --git-path info/exclude)
if [ -z "$EXCLUDE" ]; then
  echo 'not inside a git repo — do not write the tracking file here' >&2
elif ! grep -qxF '.reviews/' "$EXCLUDE"; then
  echo '.reviews/' >> "$EXCLUDE"
fi
```

The non-empty check is not decoration. Run outside a repo, `git rev-parse` fails
and leaves `$EXCLUDE` empty; a one-liner that appends unconditionally then writes
`.reviews/` into a file named `""` in the current directory instead of failing.

`.git/info/exclude`, not `.gitignore`. The exclude file is local to the clone, so
review state never shows up as a repo modification, never lands in a commit, and
never has to be explained to anyone reading the PR.

Resolve the path with `git rev-parse --git-path info/exclude` rather than writing
`.git/info/exclude` literally. In a linked worktree, `.git` is a *file* pointing at
the real git dir, not a directory — the literal path doesn't resolve and the
command fails outright, silently skipping the exclusion. `info/exclude` also lives
in the repo's shared common git directory, not a per-worktree location, so the
entry one worktree adds applies to every worktree of that clone. This is intended,
not a workaround: `.reviews/` should stay untracked everywhere the repo is checked
out, and there is no per-worktree variant of this file to use instead.

## Identity

Findings are `DR-001` upward, numbered in the order the first run reports them.
Human-verification actions are `HV-001` upward in their own sequence.

**IDs are never reused and never renumbered.** A later run continues from the
highest ID already present. An ID that can change is an ID nobody can safely put
in a commit message or hand to another person.

## Anchors

Every finding records four things: the path, the line number, **the text of the
anchored line**, and the head sha the anchor was taken at.

Re-runs match on line text first and line number second. Without the text, the
first applied fix shifts every anchor below it — findings quietly start pointing
at unrelated code and the whole file rots with nothing to signal it.

## Tags

One tag per finding, from this closed set:

| Tag | Source |
|---|---|
| `instance-scoping` | `references/data-layer.md` §1 |
| `schema-break` | `references/data-layer.md` §2 |
| `permission` | `references/permissions.md` |
| `pii` | `references/support.md` §3, and the client-content-through-`__()` gate in `references/localization.md` |
| `l10n` | `references/localization.md` — unwrapped strings and missed pseudonyms only |
| `bundle` | `references/bundle.md` |
| `placement` | `references/placement.md` |
| `agent-smell` | `references/agent-smells.md` |
| `generic` | the `SKILL.md` §3 pass |

The set is closed on purpose. Across reviews the column answers which reference
files actually earn their keep; an open vocabulary answers nothing.

The one split that is not by file: client content reaching `__()` is tagged
`pii`, not `l10n`, even though the rule lives in `localization.md`. It is a data
disclosure that happens to travel through the translation pipeline, and filing
it as `l10n` buries a Blocker among the string-wrapping nits.

## Structure

```markdown
# Review: PR #1234 — Rename Activity.StatusCode
Base release/2026.8 · 16 files · head 4f2a1c9

Run 1  2026-08-07  4f2a1c9  11 findings
Run 2  2026-08-08  9bd3e02  re-review cycle 1 · 5 fixed · 1 withdrawn · 2 new

Blocker 1 · Should fix 5 · Consider 4 · Human checks 3
Open 4 · Fixed 5 · Won't fix 1 · Withdrawn 1

## Verification

| Command | Result |
|---|---|
| `just msbuild DevResults.Core` | 0 errors, 3 pre-existing warnings |
| `just vstest DevResults.Core.Tests.dll` | 412 total · 412 passed · 0 skipped |

## Findings

| ID | Sev | Conf | Tag | Summary | Anchor | Disposition | Outcome |
|----|-----|------|-----|---------|--------|-------------|---------|
| DR-001 | Blocker | Verified | instance-scoping | Query misses InstanceID | Foo.cs:88 | Fix | Fixed 9bd3e02 |
| DR-002 | Consider | Candidate | l10n | Bare literal in toast | Bar.ts:41 | Won't fix | Won't fix |
| DR-003 | Should fix | Verified | agent-smell | Predicate duplicated from GetResults | Foo.cs:140 | | Open |

DR-001 and DR-002 have been triaged. DR-003 has not: its `Disposition` cell is
empty and its `Outcome` is `Open`. That is what an untriaged row looks like, and
it is the state every row is in when a review first writes the file.

### By file
- `DevResults.Core/Foo.cs` — DR-001, DR-003, DR-004
- `ng/src/bar.ts` — DR-002

<details>
<summary>DR-001 · Blocker · Verified · instance-scoping</summary>

**Anchor** `DevResults.Core/Foo.cs:88` @ `4f2a1c9`
`var rows = ctx.Activities.Where(a => a.StatusCode == code)`

**What** The query filters `Activities` with no `InstanceID` predicate.
**Why** `Activity` is an `IInstancedContentObject`; this returns rows from every
tenant.

**Proposed** Fix — add `&& a.InstanceID == instanceId`.
**Disposition** Fix · set 2026-08-07 · human
**Outcome** Fixed 9bd3e02 — predicate added, `ActivityQueryTests` extended.
</details>

<details>
<summary>DR-003 · Should fix · Verified · agent-smell</summary>

**Anchor** `DevResults.Core/Foo.cs:140` @ `4f2a1c9`
`where i.IsActive == null || i.IsActive == true`

**What** The active-indicator predicate is copied from `GetResults` rather than shared.
**Why** A future correction to one copy leaves the other wrong.

**Proposed** Discuss — a shared predicate is worth it only if the author agrees.
**Disposition**
**Outcome** Open
</details>

## Human verification

| ID | Action | Owner | Disposition |
|----|--------|-------|-------------|
| HV-001 | Search client custom queries for `Activity.StatusCode` | Data Reviewer | Open |
| HV-002 | Load the app minified and confirm the new service resolves | Engineer Reviewer | |

## Coverage

| Dimension | Looked | Result |
|---|---|---|
| Instance scoping | yes | 1 finding (DR-001) |
| Permissions | no | no permission surface in diff |
```

Owner values for `HV-` rows come from the PR template's three roles: `Submitter`,
`Data Reviewer`, `Engineer Reviewer`.

HV-001 has been walked and deliberately left open; HV-002 has not been asked
about at all. The difference is the empty cell, exactly as in the findings table.

## Rules

- **Withdrawn findings stay in the file** with the premise that turned out to be
  wrong (`SKILL.md` §7). Deleting them hides the correction from anyone who
  already read the review.
- Valid `Outcome` values: `Open`, `Fixed <sha>`, `Fixed (auto) <sha>`,
  `Needs recheck`, `Withdrawn`, `Won't fix`.
- **The `Disposition` column is empty until triage sets it.** A review never
  writes it. The review's recommendation goes in the `**Proposed**` field of the
  finding's `<details>` body and nowhere else — not in the column, not in the
  summary table.
- **An empty `Disposition` is the untriaged marker.** It is the only thing that
  tells a later session the row still needs a human, so an agent proposal written
  into that column makes an untriaged finding indistinguishable from an accepted
  one — and the next session will apply it as though a human had agreed. Write a
  new finding as `Disposition` empty, `Outcome: Open`.
- **Disposition provenance format:** when triage fills the `<details>` field, it
  writes `<value> · <ISO date> · <who>`, as in
  `**Disposition** Fix · set 2026-08-07 · human`. The summary table's
  `Disposition` cell carries the bare value only.
- Valid `Disposition` values for `HV-` rows — a closed set of its own, and not
  the finding dispositions:

  | Value | Means |
  |---|---|
  | *(empty)* | Not yet asked about. The untriaged marker, same as a finding row. |
  | `Done` | The action was carried out. |
  | `Not applicable` | Asked, and the action turned out not to apply. |
  | `Open` | Asked, and deliberately left open. It goes to the close-out handoff. |

  A review writes new `HV-` rows with `Disposition` **empty**, never `Open` —
  otherwise "nobody has been asked" and "asked and left open" look identical and
  an abandoned walk reads as a finished one. Reassignment is not a value: it
  rewrites the `Owner` cell and leaves `Disposition` `Open`.
- **Each re-review cycle appends its own run-log line, marked as one** —
  `Run 2  <date>  <sha>  re-review cycle 1 · …`. The cycle count is state like
  everything else here: the file is where the cap is counted from, because a
  count held in a session's head resets to zero at the next session and stops
  being a cap at all.

This file describes the artifact and nothing else. Rules about *what to do* with
it — write-through timing, what an empty review means — belong to
`references/triage.md` and `SKILL.md` §7 respectively. Do not restate them here.
