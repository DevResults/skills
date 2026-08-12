<!-- last-verified: 2026-08-07 -->

# Triage

Turning a review into decisions and then into commits. Two workflows over the
one tracking file described in
[tracking-file.md](tracking-file.md): a human wizard, and an
optional agent first pass.

Never start either without being asked. The review phase that offers triage
offers; the human accepts.

## Dispositions

| Disposition | Meaning |
|---|---|
| `Fix` | The agent applies it. May carry a free-text instruction. |
| `Defer` | Real, but a followup. Collects into the close-out handoff. |
| `Won't fix` | Accepted, with a recorded reason. |
| `Withdraw` | Not a real finding. |
| `Discuss` | Needs the PR author before anyone acts. |
| `Revert` | Auto-fixed rows only — undo the agent's fix. |

`Won't fix` and `Withdraw` are **not** the same and must not be collapsed.
`Won't fix` says the finding was right and the team accepts the cost.
`Withdraw` says the *review* was wrong. Only the second one tells you this skill
needs fixing, and merging them destroys the only feedback signal it has.

A `Fix` may carry a redirect — *"fix it, but use the existing helper"*. Record it
verbatim in the finding's block; it is what the fixer is handed, and paraphrasing
it loses the instruction.

## Entry

Triage runs when the human asks, either straight after a review or later against
an existing tracking file with no re-review at all.

Resuming: read the file and check **both** tables, in order.

1. The findings table — start at the first finding whose `Disposition` is empty.
2. Then the `HV-` table — start at the first row whose `Disposition` is empty.

Triage is complete only when no row in either table has an empty `Disposition`.
An `HV-` row reading `Open` has been asked about and deliberately left open; an
empty one has never been put to anyone. Checking only the findings table declares
a half-finished run finished, and the `HV-` items are the ones most likely to be
dropped in the first place. Do not re-ask anything already dispositioned.

A review with zero findings and zero `HV-` items skips triage — and per the
review phase that produced it, that outcome is a signal the review went wrong,
not a pass.

## Step 1 — roster and bulk accept

`AskUserQuestion` allows four options per question, so a roster of eleven
findings cannot be a menu. Put the proposals in the **message body** as a compact
table, and ask one question about the whole set:

```
DR-001  Blocker     instance-scoping  → propose Fix     (add missing scope predicate)
DR-002  Should fix  schema-break      → propose Discuss (is this column public?)
DR-003  Consider    l10n              → propose Fix     (extract to resource key)
```

> **Accept all as proposed · Walk Blockers + Should-fix · Walk everything · Other**

"Other" is where exceptions get named — *"all but DR-003 and DR-007"*. Anything
accepted in bulk is written straight to the file; anything pulled out goes to
step 2. For an already auto-fixed row, "accept as proposed" means **Keep** — the
code stands and the row's `Outcome` is unchanged. Reverting one is always an
exception the human names, never something a bulk answer does.

**A bulk-accepted row is written through step 2's mapping tables**, exactly as if
the human had pressed that proposal's button in the walk. Accepting a proposed
`Won't fix` in bulk lands `Disposition` `Won't fix` and `Outcome` `Won't fix`,
the same as walking it. Do not derive the values here — the mapping is defined
once, in step 2, and a second copy is how a bulk-accepted row and a walked row
start disagreeing.

A review whose proposals are right is triaged in one answer. A review whose
proposals are wrong loses nothing.

## Step 2 — walk the exceptions

One finding per message, with full context in the body: the anchor and its line
text, what is wrong and why it matters, and the proposed patch as a diff.

Four buttons — **Fix · Defer · Won't fix · Withdraw** — and free-text "Other"
carries `Discuss` and any redirect. Every button maps onto the closed
disposition set and the closed `Outcome` set in
[tracking-file.md](tracking-file.md) — **write the mapped values, never the
button label**:

| Button | Disposition | Outcome | The code |
|---|---|---|---|
| Fix | `Fix` | stays `Open` | unchanged for now — step 4 hands it to remediation |
| Defer | `Defer` | stays `Open` | unchanged; the close-out handoff carries it |
| Won't fix | `Won't fix` | `Won't fix` | unchanged, deliberately |
| Withdraw | `Withdraw` | `Withdrawn` | unchanged; nothing was ever applied |

`Fix` **must not** jump straight to `Fixed`. The human asking for a fix is not a
fix: the row stays `Open` until remediation lands and the evidence is checked,
and only then does it become `Fixed <sha>`. A row written `Fixed` at the moment
the button was pressed is a row the re-review will pass over as already closed,
so a fix that was never applied — or applied wrongly — is never caught.

"Other" carrying `Discuss` writes `Disposition` `Discuss` and leaves `Outcome`
`Open`: the PR author has not answered yet, so nothing about the code is
settled. A redirect rides on `Fix` and changes neither value.

`Won't fix` records the reason in the finding's `<details>` body; the value alone
says nothing to the next reader about why the team accepted the cost. `Withdraw`
records the premise that was wrong, and the row stays in the file — a withdrawn
finding is kept visible per [tracking-file.md](tracking-file.md), not deleted.

Auto-fixed rows get a different four, because the code has already changed.
Same rule — the mapped values get written, never the button label:

| Button | Disposition | Outcome | The code |
|---|---|---|---|
| Keep | `Fix` | unchanged `Fixed (auto) <sha>` | stands |
| Revert | `Revert` | `Open` | reverted; the finding stands unfixed |
| Fix differently | `Fix`, carrying the redirect | `Open`, then `Fixed <sha>` once reapplied | reverted, then fixed the human's way |
| Withdraw | `Withdraw` | `Withdrawn` | **reverted** |

Reverting a row always means a **new revert commit on top** — never a reset and
never a history rewrite, because the branch under review is normally already
pushed. It only works per row if each auto-fix was committed on its own, which is
part of the agent first pass's contract.

`Withdraw` reverting the code is deliberate, and it is the only disposition that
touches the tree. A withdrawn finding was never real, so the edit made on its
strength has nothing left justifying it — leaving it in would put a change in
the diff that no finding accounts for, which is exactly what the next reviewer
cannot explain.

Do not batch these. The bulk accept already handled the easy volume; what is left
is what the human pulled out for a reason.

## Step 3 — human-verification items

A second walk over the `HV-` rows, one row at a time. Four buttons, mapping onto
the closed `HV-` disposition set in
[tracking-file.md](tracking-file.md) — **write the mapped value, never the button
label**:

| Button | Writes |
|---|---|
| Done | `Disposition` `Done` |
| Not applicable | `Disposition` `Not applicable` |
| Assign | the chosen owner into `Owner`; `Disposition` `Open` |
| Leave open | `Disposition` `Open` |

`Assign` takes an owner from whatever role vocabulary the review wrote into the
file — the wizard displays owners, it does not define them.

Every button writes something. A row is never left empty once it has been asked
about, because empty is what marks a row nobody has reached yet, and this walk is
the one most likely to be abandoned part-way.

These are the items most likely to be forgotten today, because they are prose in
a section nobody re-reads.

## Step 4 — execute

Hand every finding dispositioned `Fix` to the host skill's remediation phase,
then run the re-review.

## Write-through

**Write the file after every answer, not at the end.** A wizard abandoned halfway
must lose nothing — that is the entire meaning of "resumable" here. There are no
concurrent writers; do not design for them.

---

<!-- Everything below this line is DevResults-specific. Everything above it is
     portable: if the wizard is ever extracted into a standalone skill, the
     split is here. -->

## Agent first pass — `--fix-first` only

Off by default. Without the flag, the review proposes and changes nothing.

With it, apply **mechanical** fixes before the wizard opens. The discriminator:

> **If proving the fix works requires a test, the fix is not mechanical.**

| May auto-fix | Never auto-fix |
|---|---|
| Dead code, unused imports, leftover debug output | Anything at `Blocker` severity, without exception |
| A bare literal moved to a resource key | Adding an `InstanceID` predicate or a permission check |
| File placement moves per [placement.md](placement.md) | Broadening a `catch`, changing a query |
| An explicit DI annotation for the minifier ([bundle.md](bundle.md) §1) | Anything whose correctness needs a test |
| Convention alignment where the convention was `Verified` | Anything at `Candidate` confidence |

**The "May auto-fix" column is closed on purpose**, exactly like the tag set. It
is five entries, not five examples: if a fix is not one of them, it is not
auto-fixable, however mechanical it looks and however `Verified` the finding is.
A rename, a signature tidy-up, a "surely harmless" reorder — none of these are on
the list, and reasoning that they belong in spirit is how a first pass turns into
an unrequested refactor the human has to review instead of the PR. Propose it
instead; the human has a `Fix` button.

Two preconditions, both checked before the first edit:

- **The working tree must be clean.** Run `git status --porcelain`; if it prints
  anything, do not auto-fix. Say why and fall through to the wizard with nothing
  applied. Per-row `Revert` depends on each auto-fix commit containing only that
  fix, and a dirty tree puts someone else's uncommitted work in the first commit.
- **Never touch a file outside the reviewed diff.** The finding's anchor names
  the file; if the fix wants to change any other file, it is not mechanical and
  it is not in scope for this pass.

This is the same boundary as the no-speculative-fixes rule in `SKILL.md` §9 and
the discriminating-test rule in [agent-smells.md](agent-smells.md) §7, applied
before a human is in the loop rather than after.

**Auto-fixes are never invisible.** Each lands as `Fixed (auto) <sha>` and shows
up in the step-1 roster with `Revert` available. An auto-fix the human never sees
would invert the review: they would end up reviewing the agent instead of the PR.

An auto-fixed row's `Disposition` stays **empty** until the human answers for it.
The pass changes the `Outcome`, never the `Disposition` — applying a fix is not
the same as being allowed to keep it, and a row this pass marked as decided is a
row the next session would skip without ever showing the human what was changed.

### One commit per auto-fix

**Each auto-fix is its own commit, holding that finding's change and nothing
else.** This pass is explicitly exempt from `SKILL.md` §9's "one commit per
coherent group of findings" — that rule is for remediation the human already
agreed to, where grouping aids the reader. Here the human has not agreed to
anything yet, and step 2 offers `Revert` per row. Per-row Revert needs a per-row
sha: group three auto-fixes into one commit and reverting the one row the human
rejected silently undoes the two they kept. Record each row's own sha in its
`Fixed (auto) <sha>` outcome.

### How a revert is performed

**Always `git revert <sha>` — a new commit on top.** Never `git reset`, never
`--amend`, never a rebase or any other history rewrite. `SKILL.md` §1 detects
PRs through `gh`, so the normal case is a branch that has already been pushed;
rewriting its history breaks every clone that pulled it and forces the author to
sort out a diverged branch they did not create.

**If the revert conflicts, stop.** Per-row commits make this likely — the fix
being reverted and a later fix can touch the same lines. Leave the tree exactly
as git left it, report the conflict and the sha to the human, and let them
resolve it. Never fall back to `git reset`, `--amend`, a rebase, or any other
rewrite to get around the conflict; the reason those are forbidden does not stop
applying because the easy path failed. Until the revert lands, the row's
`Outcome` is `Needs recheck` — the fix is still in the tree, so the row is not
reverted and not `Open` — and its `<details>` body says a revert of `<sha>` is
pending on a conflict. Set the `Disposition` the human chose; it was answered.

Bookkeeping after a revert that landed cleanly:

- The revert commit stays in the history alongside the auto-fix commit. Both are
  visible; nothing is erased. Note the revert sha in the finding's `<details>`
  body.
- **Revert** → `Disposition` `Revert`, `Outcome` back to `Open`. The finding is
  real and now unfixed; it carries forward to close-out like any open row.
- **Withdraw** → `Disposition` `Withdraw`, `Outcome` `Withdrawn`. The row stays
  in the file with the premise that was wrong.
- **Fix differently** → revert, then apply the human's redirect as a further
  commit; `Outcome` goes `Open` and then `Fixed <sha>` with that new sha.

## Re-review

After fixes land — from either workflow — the fixes are new code and get the same
review the PR got.

**Default:** run `SKILL.md` §2–§6 over `git diff <pre-fix-sha>...HEAD`, routed
reference files included.

**`--full`:** re-run from §1 over the whole diff instead, preserving every
existing ID.

Two outputs either way:

1. **New findings** get new IDs and prefix their `Summary` with
   `from-fix DR-NNN`, naming the finding whose remediation introduced them. Their
   `Tag` still comes from the closed nine-value set — `from-fix` is not a tag.
   That chain is the point: a bug the fix created should point at what caused it.
2. **Every row dispositioned `Fix` is verified mechanically.** Rows dispositioned
   anything else were not fixed and are not checked this way. The anchored line's
   text must have actually changed **and** §6 must be back to baseline before the
   row becomes `Fixed <sha>`. Anchor untouched but the fix claimed complete →
   `Needs recheck`. Never close a row on a claim.

   When §6 was legitimately skipped for a docs-only diff, "back to baseline"
   means the diff is still docs-only: check that the fix commits added no code
   file. If a fix touched code, §6 stops being skippable — build and test the
   projects it touched and record the result, and note in the file that the
   baseline was established at the fix, not at the original review.

**Cap: two fix → re-review cycles.** Then stop and report whatever remains.
Uncapped, an agent chases its own tail through cycle five and the human learns
nothing they could not have learned at cycle two.

**Count the cycles from the file, never from memory.** Each re-review appends a
run-log line marked as one (`re-review cycle N`, per
[tracking-file.md](tracking-file.md)); the cap is reached when the file already
holds two such lines. A count carried in the session's head is zero again after
any session boundary, which is the same as having no cap.

### New findings go back through triage

A re-review's new findings are findings like any other: `Disposition` empty,
`Outcome: Open`, a proposal in `**Proposed**`. **They re-enter triage at step 1
with the human and are never applied on the strength of their own proposal** —
an agent that fixes what its own fix broke, on its own say-so, is reviewing
itself. Offer the next cycle with the new roster. If the human declines it, or
the cap is already reached, close out with those findings open.

### Close-out

One counts line, then the work:

```
5 fixed · 1 auto-reverted · 2 deferred · 1 won't fix · 1 withdrawn · 3 open
```

Then the open findings with owners, then the outstanding `HV-` checklist. That
list is the handoff — it is what someone picking this up tomorrow reads first.
