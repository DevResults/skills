# DevResults skills

Shared DevResults agent skills live in this repository.

Install them with the open skills CLI:

```bash
npx skills add DevResults/skills
```

You'll be able to select which skills you want to install.

If you're using Claude Code or Pi, you'll need to add these manually to the install targets.

Choose `Global` installation scope and `Symlink` installation method.

If the skills in the repo change you'll need to reinstall them.

## Adding skills to this repo

Skills should be stored under `skills/<skill-name>/SKILL.md`. Each `SKILL.md` needs YAML frontmatter with `name` and `description`, followed by concise instructions. Put detailed reference material in `references/`, reusable scripts in `scripts/`, and output templates or static assets in `assets/` inside that skill folder.
