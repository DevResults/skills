<!-- last-verified: 2026-08-06 against DevResults main. Confirm cited paths still exist before relying on them. -->

# Support and operability

This is the half a code-focused reviewer skips entirely. The PR template's Data
Reviewer role is two lines; this is what those lines mean.

**Runs on every review.**

## 1. Can support diagnose this from "it's broken"? — lead with this

When this fails for one client, is there a log line, an audit entry, or an error
the user can quote back?

If the only symptom is "the number is wrong" or "the page is empty," support
cannot triage it and it becomes an engineering escalation. This single question
surfaces more real problems than any other item in this file, and nobody asks it
during code review.

Concretely: on the failure branch of new code, does anything get recorded that a
support engineer could search for?

## 2. Will this generate tickets?

- Silent failure — the operation no-ops and the UI looks fine.
- A changed default that affects users who didn't ask for it.
- A confusing empty state, or a control that appears without explanation.
- A global behavior change with no in-app cue.

A feature-flagged rollout usually answers this. A global behavior change usually
doesn't.

## 3. PII in exceptions and logs — HARD GATE

On the PR template, and a **Blocker** when tripped.

Does any new log line or exception message interpolate:

- contact names or email addresses
- result values or indicator data
- document names or contents
- anything from a client's own records

Log identifiers, not contents. `Contact #4821` not `brent@example.org`.

Logs and exceptions are two of the three destinations. The third is the
translation pipeline: anything handed to `__()`, `__html()`, or the `| __`
filter is persisted to `dbo.LanguageStrings` and machine-translated by Google.
Same class of finding, same `pii` tag — see `localization.md`.

## 4. Does it need KB, release notes, or client comms?

The PR template asks for tasks to be created for these. The trigger is: **could
a user notice this?** If yes, flag it.

The review's job is to flag, not to write. Put it in the Human verification
section as an action.

## 5. Admin foot-guns

Can a client admin configure this into a broken state? DevResults is unusually
configurable — custom queries, dynamic tables, pseudonyms, per-instance feature
flags, group permissions. A new setting that can be set to something incoherent
will be.

## 6. Data written in the intermediate state

Stacked PRs deploy in sequence, and the gap is real. If PR A starts populating a
column and PR B changes what that column means, rows written while A is deployed
alone carry the old meaning and nothing re-examines them.

Ask, for any queued, scheduled, or persisted work the diff touches:

- What is already in flight when this deploys?
- Does anything re-read those rows under the new rules?

The answer is either "these ship together" or a specific cleanup — a queue
drain, or a statement like
`UPDATE AsyncRequests SET LanguageCode = NULL WHERE CompletedOnUtc IS NULL`.
Put the concrete one in Human verification. "Watch out for ordering" is not an
answer.

## 7. Behavior against real client data

Does this work against ten years of messy production data, not a clean test
instance?

- Nulls in columns the new code assumes are populated
- Orphaned rows and broken relationships
- Records created before the feature existed
- Soft-deleted rows (see `data-layer.md`)
- The largest client, not the demo instance

Most of this can only be confirmed by a human against a real instance — so when
it matters, it belongs in the Human verification section as a specific
instruction, not a general worry.
