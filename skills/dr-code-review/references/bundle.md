<!-- last-verified: 2026-08-06 against DevResults main. Confirm cited paths still exist before relying on them. -->

# Production bundle

The build is **Vite 8 / Rolldown / Oxc** (`DevResults/vite.config.ts`), migrated
off Webpack. This is a failure class that does not exist in dev: the code works
under `just watch` and breaks in production, because production minifies.

The underlying question behind every check here: **did the author only ever run
`just watch`?**

## 1. AngularJS DI annotation — the common one

Any new service, controller, directive, filter, or factory using **implicit DI**
(parameter-name injection) breaks under mangling. Requires `$inject` or array
notation.

`keepNames: true` does **not** save you here. It preserves `Function.name` and
`constructor.name`; it does not preserve *parameter* names.

Treat implicit DI as the default suspicion for any new AngularJS registration.
It is the most common way this class of bug ships.

## 2. Runtime name reliance

From the config's own comment:

> `RepoBase` builds its API route from the repo class name
> (`WidgetRepo` → `/api/Widgets`). Vite's default Oxc minifier mangles those
> names, yielding bogus routes like `/api/Pa` (404).

Hence `keepNames: true`. So:

- New code reading `constructor.name` or `Function.name` — flag it, and check it
  is covered by `keepNames` rather than assuming.
- A new `*Repo` class whose route is derived from its name — confirm the derived
  route is what you expect.
- Anything else deriving behavior from an identifier's spelling at runtime.

## 3. Vite config changes

Two rules:

- A `vite.config.ts` change must be tested with a **fresh** Vite start.
- **A watch process left running in the VS Task Explorer across a branch switch
  silently serves the old config.** This is the mechanism behind "works for me"
  reviews on build changes. If the diff touches the config, the human
  verification section should say to stop the watcher and restart it.

The config also contains a `renderChunk` patch that fails loud if a bundled
helper's shape changes. If the diff touches that area, or a build starts failing
with a shape-mismatch error, read the surrounding comments before "fixing" it.

## 4. New entry points and chunking

Anything touching entry config or `manualChunks` needs a real production build
(`just build-client`), not just watch mode. Bundles are emitted to
`Web/Scripts/dist/` and served from `<site>/Web/dist/` via `BundleManagement`.

## 5. Bundle weight

A new dependency landing in a shared chunk costs every page load. Ask whether it
is needed, whether a lighter option exists, and whether it could be lazily
loaded. See the repo's `package-json-changes` skill for the sanctioned process;
dependencies install via pnpm workspaces from the repo root.

## Escalation

When any of 1–5 fires, put the instruction in the Human verification section
rather than leaving it to instinct:

> Run `just build-client` and load the app minified. This PR adds
> `ng/services/RiskScoreService.ts` with implicit DI.
