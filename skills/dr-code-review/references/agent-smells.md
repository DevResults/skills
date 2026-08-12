<!-- last-verified: 2026-08-06 -->

# Agent-authored code smells

**This pass runs on every review**, human- or agent-authored. On human code it
costs a paragraph. On agent code it is the reason this skill exists.

The repo works from `specs/` with a `planning-implementation` skill, so
spec-driven agent output is the norm — and it fails in predictable ways. All of
these produce code that *works*, which is why ordinary review misses them.

## 1. One call site of twelve — check this first

The fix was applied where the spec pointed, not everywhere the pattern occurs.
This is the single most damaging item on the list: it ships a pilot and calls it
a feature, and nobody notices until a client hits the eleven untouched paths.

**The check is mechanical.** For each behavior change, search for other call
sites of the same pattern and confirm they were considered. If they were
deliberately left, the PR should say so.

Overlaps with `surfaces.md` — that file is the same instinct applied to domain
concepts rather than call sites.

## 2. Spec-scoped comments

```
// as requested, now also handles the archived case
// per the spec, we skip validation here
// NEW: added risk level
```

A comment that only makes sense to someone holding the spec is noise to everyone
else, forever. Comments should explain the system, not the task that produced
the change. `Should fix` — cheap to remove, expensive to accumulate.

## 3. Spec-scoped naming

`handleNewRequirement()`, `V2Service`, `EnhancedFoo`, `ImprovedValidator`. Names
that describe the change rather than the thing. Same root cause as #2.

## 4. Parallel patterns

A new helper beside an existing one that does the same job — because the author
searched for the wrong term and concluded nothing existed. Ask whether the
existing one was inadequate or merely unfound.

## 5. Scaffolding left behind

Debug logging, commented-out alternatives, `TODO`s the agent wrote for itself,
unused imports, a test file with a skipped placeholder.

## 6. Over-abstraction

A strategy interface with one implementation. Generics for a two-case problem.
A config object for a function called once. Agents reach for extensibility that
nothing has asked for.

## 7. Tests that assert the implementation

Written from the diff rather than the requirement: they mirror what the code
does, pass immediately, and catch nothing. A coverage-shaped agent satisfies
"increases test coverage" vacuously.

**The check:** would this test fail if the requirement were implemented a
different but correct way? If yes, it tests the implementation. Would it fail if
the requirement were violated? If no, it tests nothing.

**Answer that check by running it, not by reading.** Delete or revert the code
under test, run the assembly, and see what happens. A test whose comment says
"the failed resolution is cached" but which only asserts `Assert.Null(...)`
twice will keep passing with the cache field deleted — and you only learn that
by deleting it. Restore afterwards and confirm the baseline.

Without that experiment the finding is a `Candidate`, not `Verified`.

The same experiment is what closes the finding. When a replacement test is
written, revert the fix, capture the failure, and quote it:

```
Expected: 1
Actual:   4
```

`Actual: 4` says exactly what the code would have cost. A replacement test that
was never seen to fail is the same smell wearing new clothes.

## 8. Confidently wrong comments

A comment asserting behavior the code doesn't have — a stale invariant, a
misdescribed parameter, a claimed guarantee. Worse than no comment, because
reviewers trust it and stop reading the code.

**The check:** for each comment in the diff making a factual claim, confirm the
adjacent code actually does that.
