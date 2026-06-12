# Writing great "How To Test" instructions

Guidance for the `### How To Test` section of a PR template. Derived from
reviewing 120+ merged PRs. Goal: a reviewer who has never seen the change can
reproduce the relevant scenario and confirm it works — including the cases that
should *fail*.

> Some examples below come from DevResults (ASP, instances like `example`/
> `demoproject`/`demoenterprise`, feature flags, roles, data tables, indicators).
> Treat them as illustrations of the principle — the rules apply to any repo.

## Core rules

1. **Open with setup/preconditions, not step 1 of the happy path.** Call out
   anything the reviewer must configure first, in its own block:
   - Feature flags (e.g. "Turn on ASP", "enable the Data Table Background Refresh feature")
   - User/group/permission setup and impersonation
   - Which instance to use (`example`, `demoproject`, `demoenterprise`, etc.)
   If the reviewer can't reproduce the starting state, the rest is wasted.

2. **Use numbered steps.** Group multi-scenario tests under bold headers
   (e.g. `**With ASP enabled**` / `**With ASP disabled**`, or
   `**Testing Indicator Data**`). For permission-heavy work, a checkbox matrix
   of (role × access level → expected) doubles as a self-review checklist.

3. **State the expected result for every step, concretely.** Not "import the
   spreadsheet" but "expect an error that the columns exceeded their limit" or
   "all tables refresh with a `RequestedBy` of `-1`". A step without an
   assertion isn't testable.

4. **Give concrete, copy-pasteable test data:**
   - Sample strings (overflow strings, diacritic examples like `Labé`/`Måmŏü`)
   - Sample SQL to seed/mutate state
   - Sample JSON payloads for API endpoints
   - Direct links to specific test objects (named indicators, instances)
   When you reference a specific ID from your own DB (`CustomQueryID=351`), note
   that the reviewer's IDs will differ, or phrase it as "find a record where…".

5. **Include verification queries for anything not visible in the UI.** If the
   effect lands in the database, give the query
   (`select top 25 * from Changes order by ChangeID desc`). Don't make the
   reviewer guess how to confirm a DB-level change.

6. **Contrast with `main` for bug/regression fixes.** Tell the reviewer what the
   broken behavior looks like ("On `main` this throws…", "unchanged from `main`")
   so they can confirm the fix actually changed something.

7. **Cover negative and permission cases.** Explicitly test what should *not*
   happen: hidden tabs, disabled buttons, server-blocked actions. A good move:
   change a permission *without reloading* and confirm the server still blocks
   the action, then reload and confirm visibility. Reviewers won't test these
   unless you list them.

8. **Mark deeper/edge checks as `Optional:`** so reviewers can triage effort.

9. **For refactors / no-behavior-change PRs, be honest but still give a
   poke-list.** Don't write "nothing to test" and stop. Say "direct replacement,
   covered by tests, but worth poking [these endpoints/pages]" and, where
   relevant, "see if you agree with [design decision]".

10. **For API-only PRs, list each endpoint as a checklist with method + path**
    (`GET /api/...`, `POST /api/...`) and include a sample payload for writes.

## Anti-patterns (avoid)

- **Leftover template boilerplate** — delete the placeholder
  "Instructions how to specifically replicate relevant scenario" prompt text.
- **Broken/garbled step numbering** — read the rendered list before submitting;
  duplicate or skipped numbers usually mean steps were edited without renumbering.
- **Empty section** — even "covered by unit tests, no manual testing needed" beats
  a blank section. Never leave `### How To Test` empty.
- **Too terse for the risk level** — "CI passes" is fine for a lint fix only;
  calibrate detail to how badly the change could break runtime behavior.

## Minimal template

```markdown
### How To Test

**Setup:** <feature flags, instance, user/permissions, impersonation>

1. <action> → <expected result>
2. <action> → <expected result>
   - Verify in DB: `<query>`
3. ...

**Negative/permission cases:**
- <what should be blocked/hidden> → <expected>

**Optional:** <deeper or edge-case checks>

<For refactors: "Direct replacement, covered by tests. Worth poking: X, Y.
See if you agree with <design decision>.">
```
