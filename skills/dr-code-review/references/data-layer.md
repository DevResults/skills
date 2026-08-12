<!-- last-verified: 2026-08-06 against DevResults main. Confirm cited paths still exist before relying on them. -->

# Data layer

DevResults is a **single-database multi-tenant** app. Non-global tables carry an
`InstanceID` column, and that column is the only thing separating one client's
data from another's.

Nothing scopes it for you.

## 1. Instance scoping — HARD GATE

`DevResults.Models/IRepository.cs`:

```csharp
IQueryable<T> CreateQuery<T>() where T : class;                    // NOT scoped
IQueryable<T> GetAllByInstance<T>(int InstanceID = 0) where T : class, IInstancedContentObject;  // scoped
```

**`CreateQuery<T>` is unscoped by default.** Assume the opposite and you ship a
cross-tenant leak. Raw SQL via `IDbConnectionFactory` is scoped by nothing at
all — every predicate is hand-written.

**The check:** a query over a type implementing `IInstancedContentObject` with no
`InstanceID` predicate is a candidate leak. Report it as a **Blocker** with
confidence `Candidate` unless you can trace the scoping.

**Bias toward flagging.** A false positive costs a sentence. A false negative is
a client seeing another client's data.

### Known-global tables

These have an `InstanceID` column that is **not used**. A missing `InstanceID`
predicate on these is fine — say so and move on:

```
CachedBlogPosts        Features               Languages              ScheduledTaskLogs
Contacts               HelpArticles           LanguageStrings        WorldAdminDivisions
CountryNames           IatiCodeListItems      OneTimeScriptLogs      WorldShapes
CurrencyCodes          IatiCodeLists          ReportingStatusCodes
CustomQuerys           IatiVocabularys        Roles
Events                 IntegrityEnforcementLogs
                       IntegrityEnforcers
```

Anything **not** on this list gets flagged for justification. Do not extend the
list from inference — if you can't tell, flag it.

### The legitimate exception

Enterprise users (`EnterpriseAdmin`, `EnterpriseAccess`) span instances by
design. A cross-instance query is correct there **if** it is gated on the
enterprise role. Confirm the gate; don't just accept the intent.

## 2. Removed or renamed tables and columns — HARD GATE

Clients write their own **custom queries** against the schema. They live in
client data, not in this repo. No compiler, no test, and no type checker catches
a rename.

Any diff that removes or renames a table or column is a **Blocker** until the
review says so explicitly and puts a search instruction in the Human
verification section:

> Search client custom queries and setup scripts for `Activity.StatusCode` —
> this PR renames it to `Activity.StatusOptionID`.

This is the PR template's "Checked custom queries & setup scripts for
removed/renamed tables & columns," which is easy to tick and expensive to miss.

## 3. Soft delete

`IContentObject.Deleted` is a soft-delete flag, and filtering is **opt-in**:

```csharp
public static T IfNotDeleted<T>(this T source) where T : class, IContentObject
```

A new query with no `Deleted` filter will return deleted rows. Usually wrong,
occasionally intended. Flag it as `Should fix` / `Candidate` and let the author
say which.

## 4. New tables

- **`DeleteAllData` stored procedure.** New tables must be added, or test
  cleanup silently leaves rows behind and tests get flaky in ways nobody traces
  back. This is on the PR template's Submitter list.
- **Two definition paths.** Entities come from either `DbSchema.xml`
  (`DevResults/Model/Entities/DbSchema/`, T4-generated) or a class inheriting
  `AbstractTableCompiler`. Check the diff used the right one for what it's
  building, and see the repo's own `database-schema` skill.
- Note: `DbSchema.xml` carries a lot of historical cruft. Do **not** review
  against attribute completeness — most attributes aren't live. Judge against
  what comparable current entities do.

## 5. Indexes

New query paths run against client tables with years of real data. "Fast on a
dev instance" means nothing.

For any new or changed query, ask whether the predicate and sort columns are
indexed, and whether an `IndexesOnly(...)` compiler was added. Report a missing
index as `Should fix` — it's rarely a blocker, and it's almost always cheaper to
add now than after a client escalation.

## 6. Generated files

`ApiModels.ts`, `FeatureCodes.ts`, `RoleCodes.ts` are T4 output.

- **Hand-edited generated file → Blocker.** It will be silently reverted on the
  next build.
- **Source changed but generated file not regenerated → `Should fix`.** The diff
  is inconsistent and the next person's build produces unrelated churn.

## 7. New fields on existing entities

New fields should be nullable or carry a sensible default. Every client database
gets the column, applied to years of existing rows. If a field is non-null with
no default, ask what the value is for records created before the feature
existed.
