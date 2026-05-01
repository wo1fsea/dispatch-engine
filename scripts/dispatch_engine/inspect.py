"""Repository discovery for Dispatch Engine."""

from __future__ import annotations

from pathlib import Path


INSTRUCTION_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    "CONTRIBUTING.md",
    "README.md",
]

PLANNING_GLOBS = [
    "specs/**/PRODUCT.md",
    "specs/**/TECH.md",
    "specs/**/*.md",
    "docs/**/*.md",
    "plans/**/*.md",
]
PLANNING_SOURCE_LIMIT = 8

VALIDATION_FILES = [
    "package.json",
    "pyproject.toml",
    "Makefile",
    "justfile",
    "Cargo.toml",
    "go.mod",
]


def inspect_repo(target: Path) -> dict:
    repo_root = target.resolve()
    instructions = _existing(repo_root, INSTRUCTION_FILES)
    planning_sources = _planning_sources(repo_root)
    validation_hints = _existing(repo_root, VALIDATION_FILES)

    return {
        "kind": "inspection",
        "repo_root": str(repo_root),
        "instructions": instructions or ["none detected"],
        "planning_sources": planning_sources or ["none detected"],
        "validation_hints": validation_hints or ["none detected"],
    }


def _existing(root: Path, paths: list[str]) -> list[str]:
    found = []
    for item in paths:
        if (root / item).exists():
            found.append(item)
    return found


def _planning_sources(root: Path) -> list[str]:
    found: set[str] = set()
    seen: set[str] = set()
    for pattern in PLANNING_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and ".git" not in path.parts:
                rel = str(path.relative_to(root))
                if rel in seen:
                    continue
                seen.add(rel)
                found.add(rel)
    return sorted(found, key=_planning_source_priority)[:PLANNING_SOURCE_LIMIT]


def _planning_source_priority(path: str) -> tuple[int, str]:
    if path.endswith("/PRODUCT.md") or path == "PRODUCT.md":
        return (0, path)
    if path.endswith("/TECH.md") or path == "TECH.md":
        return (1, path)
    if path.startswith("specs/"):
        return (2, path)
    if path.startswith("plans/"):
        return (3, path)
    if path.startswith("docs/"):
        return (4, path)
    return (5, path)
