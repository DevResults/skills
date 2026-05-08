# DevResults skills

Shared DevResults agent skills live in this repository.

Install them with the open skills CLI:

```bash
npx skills add DevResults/skills
```

To list available skills without installing:

```bash
npx skills add DevResults/skills --list
```

Skills should be stored under `skills/<skill-name>/SKILL.md`. Each `SKILL.md` needs YAML frontmatter with `name` and `description`, followed by concise instructions. Put detailed reference material in `references/`, reusable scripts in `scripts/`, and output templates or static assets in `assets/` inside that skill folder.
