import {
  existsSync,
  lstatSync,
  mkdirSync,
  readdirSync,
  readlinkSync,
  symlinkSync,
  unlinkSync,
} from "node:fs"
import { homedir } from "node:os"
import { basename, join, resolve } from "node:path"

/** Install every top-level skill in this repository into the local Codex skills directory. */
export function installSkills(): void {
  const repositoryPath = resolve(import.meta.dirname, "..")
  const destinationPath = getDestinationPath()
  const skillPaths = getSkillPaths(repositoryPath)

  mkdirSync(destinationPath, { recursive: true })

  skillPaths.forEach(skillPath => {
    installSkill(skillPath, join(destinationPath, basename(skillPath)))
  })
}

/** Get the Codex skills directory. */
export function getDestinationPath(): string {
  return join(process.env.CODEX_HOME ?? join(homedir(), ".codex"), "skills")
}

/** Get top-level repository folders that are skills. */
export function getSkillPaths(
  /** The repository root path. */
  repositoryPath: string,
): string[] {
  return readdirSync(repositoryPath, { withFileTypes: true })
    .filter(entry => entry.isDirectory())
    .filter(entry => ![".git", "node_modules", "scripts", "templates"].includes(entry.name))
    .map(entry => join(repositoryPath, entry.name))
    .filter(path => existsSync(join(path, "SKILL.md")))
}

/** Symlink a skill into the destination directory. */
export function installSkill(
  /** The source skill path. */
  skillPath: string,
  /** The destination symlink path. */
  linkPath: string,
): void {
  if (existsSync(linkPath)) {
    const stat = lstatSync(linkPath)

    if (!stat.isSymbolicLink() || readlinkSync(linkPath) !== skillPath) {
      throw new Error(`Refusing to replace existing path: ${linkPath}`)
    }

    unlinkSync(linkPath)
  }

  symlinkSync(skillPath, linkPath, "dir")
  console.log(`Linked ${basename(skillPath)} -> ${linkPath}`)
}

installSkills()
