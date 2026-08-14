<!-- last-verified: 2026-08-06 against DevResults main. Confirm cited paths still exist before relying on them. -->

# Surface inventory

The question this file answers: **is this applied everywhere it can be, or is it
a pilot?**

A new field that lands in the web UI but not the import template is a guaranteed
support ticket. This is the knowledge a five-year veteran has and a new hire — or
an agent working from a spec — does not.

## The walk

For **every new or changed domain concept** (entity, field, status, relationship),
walk this list explicitly. For each one: does it need to change, and did it?

1. **Web UI** — create, edit, list, detail. All four, not just the one the spec
   named.
2. **Public API / integrations** — is the field exposed? Should it be? Does an
   existing API response shape change (a breaking change for consumers)?
3. **Bulk import + Excel templates** — new field that can't be imported means
   clients hand-enter it for thousands of rows.
4. **Exports and reports** — does the field appear where users expect to get
   their data out?
5. **Search / filters** — is it searchable, filterable, sortable? If comparable
   fields are, this one probably should be.
6. **Notifications and emails** — does this change what gets sent, to whom, or
   how often? Will it spam anyone?
7. **Permissions model** — does the new thing need its own permission, or does it
   ride on an existing one? Riding on an existing one is a decision, not a
   default. See `permissions.md`.
8. **Audit trail / change history** — is the change tracked? A field that changes
   without history is one nobody can explain later.
9. **Deletion and archive semantics** — what happens when the parent is deleted
   or archived? Orphans, cascades, and soft-deleted rows still showing up.

## How to report it

Do not report "consider adding this to the import template" as a vague nit. Say
which surfaces were covered and which weren't:

> `Activity.RiskLevel` is added to the web UI (create/edit/detail) and the API.
> Not in the bulk import template, exports, or filters. Intentional?
> — `Should fix`, `Verified`

A concept that only landed on one or two surfaces is either a deliberate pilot —
in which case the PR should say so — or an incomplete feature. Make the author
answer which.

## Related

Several of these are configured rather than coded, and the repo's
`database-schema` and `creating-api-endpoints` skills define how. Cite them when
the diff diverges.
