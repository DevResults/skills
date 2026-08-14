<!-- last-verified: 2026-08-06 against DevResults main. Confirm cited paths still exist before relying on them. -->

# Placement

Did the code land where it belongs? A diff can work perfectly and still be in
the wrong place, and that is invisible unless someone looks for it.

## Frontend: `ng/` vs `src/`

**The frontend is all AngularJS, written in TypeScript.** This is not a
legacy/modern split — it is a fit question:

- **`Web/Scripts/ng/`** — anything that needs AngularJS (directives, services,
  repos, filters, templates).
- **`Web/Scripts/src/`** — anything that does *not* need AngularJS.

New work should normally land in one of those two. Getting it backwards — an
Angular-dependent thing in `src/`, or a framework-free utility buried in `ng/` —
is a `Consider` finding, worth naming but rarely worth blocking.

### Standing carve-outs

Do **not** flag these as misplacement:

- **d3 components** in their existing location. More are expected over time.
- Specific legacy code that needs to live where it is.

If new code lands outside `ng/` and `src/` and isn't d3, ask why.

## Backend: the real legacy split

**VB.NET Web Forms (`DevResults/`) vs. C# Web API 2 (`DevResults.Api/`)** is the
genuine legacy/modern boundary.

New code on the Web Forms side **needs a reason**. Not a ban — sometimes
touching the Web Forms page is exactly right — but the review should notice and
ask, rather than nodding at a working diff that added 200 lines to the legacy
side because that's where the agent found a similar function.

Other backend layering, for reference:

- `DevResults.Api/` — controllers and API models
- `DevResults.Core/` — business logic and repositories
- `DevResults.Models/` — EF6 context and entities
- `DevResults.Utilities/` — shared utilities

Business logic in a controller, or data access in `DevResults/`, is a
`Should fix`.

## Follow the sanctioned pattern

The repo's own skills define how things are built here: `database-schema`,
`creating-api-endpoints`, `angularjs`, `package-json-changes`,
`planning-implementation`.

**If a skill covers what the diff is doing, the diff should match it, and the
finding should cite the skill.** This costs nothing and makes the existing
skills self-enforcing.

## Did it invent a parallel pattern?

The related question, and the more common failure with agent-authored code: is
there already a helper, service, or repository that does this? A new one beside
an existing one usually means the author didn't find the existing one, not that
the existing one was inadequate. See `agent-smells.md`.
