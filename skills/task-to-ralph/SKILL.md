---
name: task-to-ralph
description: Use when the user provides a spec file and wants it broken into discrete, committable tasks written to .ralph/todo.md
user-invocable: true
---

# Task to Ralph

Break down a spec file into discrete, individually actionable tasks and write them to `.ralph/todo.md`.

## Input

A spec file path (e.g., `specs/my-feature/plan.md`). If not provided as an argument, ask the user which spec file to use.

## Process

1. **Read the spec file** thoroughly. Understand every requirement, change, and deliverable.

2. **Identify the smallest coherent commits.** Each commit should:
   - Be independently buildable and testable
   - Represent a logical unit of work (e.g., "add model class", "create API endpoint", "write tests for X")
   - Follow a dependency order — earlier tasks should not depend on later ones

3. **Create subtasks within each commit group.** Multiple steps that combine into one commit should be listed as indented subtasks under a parent task. Example:
   - A parent task like "Add FooController endpoint" might have subtasks for creating the model, writing the controller method, and adding the route.

4. **Write tasks to `.ralph/todo.md`** using the format below. Ask the user if previous tasks should be removed from the TODO, Completed, or all sections to ensure no important tasks are lost. Preserve the file structure.

## Output Format

Write `.ralph/todo.md` with this exact structure:

```markdown
**Plan:** `<spec-file-path>`

---

### TODO List

- [ ] Task 1 description
  - [ ] Subtask 1a
  - [ ] Subtask 1b
- [ ] Task 2 description
  - [ ] Subtask 2a
  - [ ] Subtask 2b
- [ ] Task 3 description

---

### Completed Tasks
```

## Rules

- Every task and subtask gets an unchecked checkbox (`- [ ]`)
- Parent tasks represent the smallest coherent commit
- Subtasks are the individual steps within that commit
- Tasks must be ordered by dependency (implement foundations first)
- Task descriptions should be specific and actionable — name the files, classes, or functions involved
- Do NOT include tasks for committing, pushing, or creating PRs — only implementation work
- If the spec has phases or sections, preserve that ordering
- Keep task descriptions concise but unambiguous
