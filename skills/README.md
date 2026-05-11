# Skills

Add each skill in its own folder here:

```text
skills/
  my-skill/
    SKILL.md
```

The `npx skills` CLI discovers `SKILL.md` files in this directory automatically.


## `/new-pr`

Assists in creating a new pull request, guiding the agent to look for a PR template and to ask which branch the PR should merge into.

Example usage:

```
# Basic
/new-pr

# Include a target branch and a reference:
/new-pr into main. Include a reference to the original task: [Optimize the thingy](https://app.asana.com/xxxxxxx)
```