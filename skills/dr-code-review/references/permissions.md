<!-- last-verified: 2026-08-06 against DevResults main. Confirm cited paths still exist before relying on them. -->

# Permissions

The recurring failure is not "we forgot permissions." It is **the UI hides the
button and everyone calls it done** — while the endpoint still answers.

## The four layers

Outside in. **Layer 1 passing does not imply 2 or 3.**

1. **Route-level role attribute** — `[AuthorizedRoles(Roles = Role.Codes.X)]` on
   the controller or action (`DevResults.Api/Controllers/`).
2. **Injected validators** — `DevResults.Core/Security/`:
   `ICurrentPermissionsValidator`, `IActivityPermissionsValidator`,
   `IIndicatorPermissionsValidator`, `IAttributePermissionsValidator`,
   `IAwardReportingPeriodPermissionsValidator`.
3. **Query scoping** — `ActivitySpecificIndicatorRepository`,
   `ActivitySpecificAwardRepository`, and friends.
4. **Client-side gating** — `Web/Scripts/src/FeatureCodes.ts`,
   `ng/services/GroupPermissionsService.ts`. **Concealment only. Never
   enforcement.**

A role attribute alone is not enforcement. If the resource is scoped to an
activity, an indicator, or an attribute, layer 1 will happily let a user reach
someone else's row.

## Three demands on any permission-touching diff

### 1. Cite the server-side check — HARD GATE

If the diff adds or changes a UI affordance gated on a permission, the review
must name the line that enforces it server-side. If you cannot find one, that
is a **Blocker**, not a question.

Look for layer 2 or 3, not layer 1. `FeatureCodes.ts` and
`GroupPermissionsService.ts` are not answers.

### 2. Walk the role matrix

Do not walk all ~43 role codes — that's theater. Walk these seven:

| Persona | Why it's on the list |
|---|---|
| Owner / Admin | the happy path everyone tests |
| Standard user, all activities | the common case |
| Standard user, subset of activities | only meaningful with `ActivitySpecificPermissions` **on** |
| Partner | separate code path — see below |
| PartnerManager | Partner-ish, not identical |
| Enterprise user, multiple instances | legitimately crosses instances |
| NoAccess / unauthenticated | the negative path, where info-leak lives |

Feature-area role codes (`Budget`, `Documents`, `IndicatorDefinitions`,
`IndicatorResults`, `Contacts`, …) get pulled in only when the diff touches
that area.

**Partner is a different code path, not a lower permission level.**
`PermissionsValidator` is full of early returns:

```csharp
if (IsPartner(contact, instance)) return false;
```

`IsPartner()` is true for both `Partner` and `PartnerManager` — both have
"limited in-app experiences." A change to normal permission logic can silently
fail to reach Partner users, or accidentally reach them. This is why the PR
template has "Tested for Partner regressions" as its own line.

### 3. `ActivitySpecificPermissions` is a per-instance feature flag

```csharp
FeatureManager.IsEnabled(Feature.Codes.ActivitySpecificPermissions, instance.ID)
```

It is not a global mode. Some clients have it on, some don't. **State which side
of the flag was reasoned about, and confirm the other side isn't broken.** A
change that only makes sense with the flag on is a regression for every client
without it, and vice versa.

### 4. Check the negative path

- What does a user without permission actually see?
- Does the error leak the existence of the record? `403` on a record the user
  shouldn't know exists is an information leak; `404` is usually right.
- Does an exception message name the resource, the owner, or the contact?
  See `support.md` — that's the PII gate.

## Cross-instance access

Enterprise users (`EnterpriseAdmin`, `EnterpriseAccess`) with access to multiple
instances are the **one legitimate reason** for a query that crosses instances.
That makes them the named exception to the `InstanceID` scoping rule in
`data-layer.md`, not a violation of it. If a diff removes instance scoping for
an enterprise feature, confirm it is actually gated on the enterprise role.
