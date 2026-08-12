# Future improvements

Not built. Recorded so the design isn't lost.

## Fan-out escalation for large or high-risk diffs

The router pass reads reference files serially. For a large diff touching
`Security/`, `DbSchema.xml`, and the Vite config at once, one agent per
reference file would go deeper.

Design as discussed, if it gets built:

- **Trigger**: the skill runs its normal router pass first, then *recommends*
  a deep pass and the human confirms. Explicit opt-in (`--deep`) always
  available. Do not auto-escalate on file count — a 40-file rename would burn
  a lot of tokens for nothing, and the human has context the diff doesn't show.
- **Shape**: one agent per reference file (permissions, data-layer, surfaces,
  bundle, localization, placement, agent-smells, support).
- **Merge rules**, which are the part that matters:
  - Every agent reports in the same findings format with mandatory `file:line`
    anchors.
  - The merging agent dedupes and orders. It is forbidden from summarizing
    findings away. Losing findings in the merge is the standard failure mode
    of fan-out reviews.
  - Fan-out never runs against a diff the main pass hasn't already read —
    otherwise every agent independently reconstructs context and you pay for
    it N times.

## Consolidate every closed set into the tracking file

Not built. The skill runs on closed sets — nine tags, six finding dispositions,
six `Outcome` values, the `HV-` dispositions — and they live in two places.
`references/tracking-file.md` owns the tags, the `Outcome` set and the `HV-` set;
`references/triage.md` owns the finding dispositions. Everywhere else cites them,
mostly correctly, and every drift found so far has been a copy of a set going
stale against its original.

The fix is structural rather than another round of corrections: every closed set
is declared once, in `references/tracking-file.md`, and every other file links to
it and enumerates nothing. That retires the whole class of drift instead of the
instances currently known.

## Other ideas

- A `--staged` mode for pre-commit self-review.
- The `InstanceID` known-global list in `references/data-layer.md` could be
  derived from the schema instead of hardcoded, if the vestigial columns are
  ever marked in `DbSchema.xml`.

## Answered

- *Which reference files fire most often?* The `Tag` column in the tracking file
  records this per finding, from a closed nine-value set. Reading it across a
  batch of `.reviews/*.md` answers the question directly — a reference file that
  never appears as a tag is either wrong or its trigger is mis-specified.

## Since built

Everything above is unbuilt. What used to be listed here and no longer is: the
triage and remediation workflows — see `references/triage.md` and
`references/tracking-file.md`.
