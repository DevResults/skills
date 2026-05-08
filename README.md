# DevResults shared skills

Shared Codex skills for DevResults work live here. Each top-level skill folder should contain a `SKILL.md` file with YAML frontmatter and focused instructions.

Use `templates/skill` as the starting point for new skills:

```bash
cp -R templates/skill my-skill
```

Then update `my-skill/SKILL.md` and `my-skill/agents/openai.yaml`.

To make these skills discoverable by local Codex, run:

```bash
pnpm install-skills
```

That script symlinks top-level skill folders into `${CODEX_HOME:-~/.codex}/skills`.
