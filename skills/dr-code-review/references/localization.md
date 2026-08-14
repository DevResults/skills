<!-- last-verified: 2026-08-10 against DevResults main. Confirm cited paths still exist before relying on them. -->

# Localization and pseudonyms

Two separate mechanisms, both required, both easy to skip because the app looks
fine in English on a default instance — and one hard gate that runs the other
way, because the pipeline that translates developer text will exfiltrate client
text just as willingly.

## Hard gate — client content must never reach `__()`

**Read this first. It is the only Blocker in this file.**

`__()` is a registration function, not a formatter. Anything it does not already
recognize gets written to a permanent store and shipped to Google. Verified end
to end:

1. `__()` → `translate()` in `Web/Scripts/core/i18n.ts`. A miss in
   `window.$dev.i18n.languageStrings` fires `POST /api/LanguageStrings` with the
   string verbatim.
2. `LocalizationProvider.GetString`
   (`DevResults.Core/Localization/LocalizationProvider.cs`) `MERGE`s it into
   `dbo.LanguageStrings`. `Name` is `nvarchar(max)` and is its own key — no
   owner, no source record, no tie to the permissions or lifecycle of whatever
   it came from. Deleting the record it was copied out of does not remove it.
3. The scheduled `Translate` worker (`DevResults/Tasks/Workers/Translate.vb`)
   calls `MachineTranslateAll()`, which walks every row with an empty
   translation and sends it to **Google Translate**
   (`DevResults.Core/Localization/TranslationProvider.cs`).
4. Every registered row is listed in the admin **Text Translations** grid
   (`Web/Scripts/ng/directives/admin/LanguageStrings.html`).

So one `| __` on a bound expression takes a contact name, a result comment, a
document title, or a custom field value; copies it out of the record it belongs
to; sends it to a third-party API no DPA covers for that content; and renders it
on an admin screen that carries none of the source record's permissions.

Server side there is a second consequence:
`PseudonymRepository.ReplaceEntireStringOrTokens` replaces the **entire string**
when it matches a pseudonym `Title`, so client text that happens to equal a
renamed term is silently rewritten before it is stored or displayed.

**This has already happened.** The Grid directive used to translate its column
headers, so every client-authored `DynamicTableColumn.Title` registered itself.
The cleanup is still in the repo, as hand-audited `DELETE` statements:
`Core/Db/Sql/Onetime/PostPopulate/20200921 Delete bad LanguageStrings.sql`.

### The rule

**`__()`, `__html()`, and `| __` take developer-authored text.** A quoted
literal is the safe form. When the argument is an expression, trace one hop to
where the value is set:

- A fixed set of strings in the code — role titles, enum labels, server-side
  error messages, feature names — is fine.
- **Anything a client can type is a Blocker.** Contact and organization names,
  activity/indicator/award titles, result comments and narrative, document
  names, custom field values, dynamic table column titles, group and tag names,
  saved query names, pseudonym alternatives, imported spreadsheet content.

If you cannot tell in one hop where the value comes from, that is a `Candidate`
finding plus an `HV-` action, not a pass.

**Existing call sites are not a defense.** Roughly thirty places already pass an
expression to `__()` or `| __`. Most are developer-authored, some are only
arguably so — `__(item.Key)` on a search result, `__(v)` on a location value
during a merge. "It's done elsewhere" is the rationalization to watch for in the
PR description and in your own reasoning; the question is what *this* value can
contain, not what the neighboring line does. If the diff's own precedent looks
wrong, say so as a separate `Consider` and leave the pre-existing code alone.

### Shapes

| In the diff | Verdict |
|---|---|
| `{{::"Save"\|__}}` | fine — quoted literal |
| `{{item.title\|__}}`, `{{::col.header\|__}}`, `{{row.name\|__html}}` | **Blocker** unless one hop proves the value is developer-authored |
| `__("Select an !~activity~!")` | fine |
| `__(row.Name)`, `__(field.label)` | **Blocker** on the same condition |
| `` __(`Showing ${n} results`) ``, `__("Showing " + n)` | Should fix — no client data, but it registers a row and fires a POST per distinct value |
| `stringFormat(__("{0} results"), n)` | fine — the template is translated, the value is interpolated after. `Web/Scripts/src/stringFormat.ts`; this is the sanctioned pattern |
| `localizer.GetString($"Deleted {contact.Name}")` (C#) | **Blocker** — interpolation collapses before the call, so the name is the key |
| `localizer.GetFormattedString($"Deleted {contact.Name}")` | fine — takes a `FormattableString`; only `template.Format` is looked up |
| `__($"…{value}…")` (VB, `Core/Localization/Localization.vb`) | **Blocker** — same collapse, and there is no `FormattableString` overload |

The two `GetString`/`GetFormattedString` rows are the ones a generic reviewer
will miss: both compile, both read identically, and only one of them keeps the
argument out of the database.

### The fix to propose

Drop the filter (`{{::item.title}}`), or split the string so the template is
localized and the client value is interpolated afterwards. Never "add the
pseudonym tokens" to client text — that is treating a data-exposure finding as a
translation nit.

### Where this shows up

Grids and column definitions built from configuration, `headerName`/`valueGetter`
callbacks, chart axis and series labels, export headers derived from data,
toast and validation messages that quote the offending value back, tooltips,
breadcrumbs, and page titles built from the record being viewed.

## Localization

`Web/Scripts/core/i18n.ts` exposes `__()` and `__html()`. Server side:
`DevResults.Core/Localization/LocalizationProvider.cs`,
`DevResults/Core/ServerToClient.vb`.

**Every user-facing literal must be wrapped.** Unwrapped text is not a
"missing translation" — it is text that can never be translated, because the
string never registers.

How registration works: `translate()` looks the string up in
`window.$dev.i18n.languageStrings`; on a miss it POSTs to `/api/LanguageStrings`
to register it and returns the English. So a wrapped string self-registers and a
bare string is invisible forever — and anything else handed to `__()` registers
just as permanently, which is what the hard gate above is about.

**The check:** any new string literal that reaches a user — labels, buttons,
placeholders, validation messages, tooltips, empty states, error messages,
column headers, export headers, email copy — wrapped in `__()` or `__html()`?

Non-findings: log messages, exception messages for developers, code identifiers,
test fixtures.

## Pseudonyms

Clients rename core terms ([help article](https://help.devresults.com/help/renaming-terms-in-devresults)).
`substitute()` in `Web/Scripts/src/pseudonyms.ts` runs **before** translation —
`__()` calls it for you. Client side it only rewrites `!~token~!` markers;
server side `ReplaceEntireStringOrTokens` also swaps a whole string that matches
a pseudonym title, which is why the hard gate above matters more on the server.

Replaceable terms are wrapped in `!~term~!`:

```
!~activity~!
```

### The terms

Singular **and** plural, capitalized **and** lower-case, wherever the text refers
to the entity:

```
activity        organization                    tag
project         indicator result comment        mechanism
location        sector                          deliverable
awarding organization                           memo
partner organization                            expenses and Disbursement
```

**The check:** does any new user-facing text contain one of these words in its
domain sense, unwrapped? "Select an activity" is wrong; "Select an !~activity~!"
is right. A client who renamed *activity* to *grant* sees "Select an activity"
and files a ticket.

Watch for the plural and capitalized forms specifically — those are what get
missed, because the author wraps the one instance they were looking at.

## Where this gets missed

- Validation and error messages — written last, reviewed least.
- Empty states and zero-result text.
- Export and report column headers.
- Email and notification templates.
- Text built by string concatenation, where the wrapping has to happen per
  fragment and often doesn't.
- Anything added to a `src/` module that runs outside AngularJS — `__()` is
  injected there via the Vite config, so confirm it's actually imported and not
  just assumed global. See `bundle.md`.

## PR template

This covers "All strings are localized" and "All pseudonyms accounted for."
Both are Submitter checkboxes, which means they are self-reported and routinely
ticked optimistically. Verify rather than trust.

The hard gate has **no checkbox**. Nothing in the template asks whether client
content reaches `__()`, and a submitter who ticked "All strings are localized"
may have ticked it *because* they wrapped a bound expression. Treat that
checkbox as a reason to look harder, not as coverage.
