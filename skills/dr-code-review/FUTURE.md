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

## Other ideas

- A `--staged` mode for pre-commit self-review.
- The `InstanceID` known-global list in `references/data-layer.md` could be
  derived from the schema instead of hardcoded, if the vestigial columns are
  ever marked in `DbSchema.xml`.

## Answered

- *Which reference files fire most often?* The `Tag` column in the tracking file
  records this per finding, from a closed set. Reading it across a
  batch of `.reviews/*.md` answers the question directly — a reference file that
  never appears as a tag is either wrong or its trigger is mis-specified.

## Since built

Everything above is unbuilt. What used to be listed here and no longer is:

- The triage and remediation workflows — see `references/triage.md` and
  `references/tracking-file.md`.
- Consolidating every closed set into one place. `references/tracking-file.md`
  now has a `## Vocabulary` section owning severity, confidence, tags, both
  disposition sets, `Outcome` and the `HV-` owner roles; every other file cites
  it and enumerates nothing.
