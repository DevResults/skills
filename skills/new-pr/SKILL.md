---
name: new-pr
description: Create a PR for the current branch using the repo's standard template
user-invocable: true
---

Create a PR for this branch using the standard template for this repo, if one exists. Ask me which branch the PR should target.

## Testing instructions

If the template has a section that calls for testing instructions (e.g.
`### How To Test`, "Steps to test", "QA notes"), fill it in following
[references/testing-instructions.md](references/testing-instructions.md) so the
instructions are reproducible and cover negative/permission cases — read it
before writing that section.

If there is no template, or the template has no section that suggests testing
instructions, ask me whether to include testing instructions before adding them.
Only add a testing section if I say yes, and follow
[references/testing-instructions.md](references/testing-instructions.md) when you do.
