"""Generate a project map for the sonos_rescue project."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src" / "sonos_rescue"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "project-map.md"

EXCLUDED_NAMES = {
    "__pycache__",
    ".pytest_cache",
    "sonos_rescue.egg-info",
    "__init__.py",
    ".git",
    ".vscode",
    ".venv",
    ".png",
}

print("# Sonos Rescue Project Map\n\n## File Structure\n")
print(f"(Output will be saved to {OUTPUT_FILE})\n")


def generate_tree(path: Path, prefix: str = "") -> list[str]:
    """Generate a tree-style representation of a directory."""
    entries = sorted(
        (entry for entry in path.iterdir() if entry.name not in EXCLUDED_NAMES),
        key=lambda item: (item.is_file(), item.name.lower()),
    )

    lines: list[str] = []

    for index, entry in enumerate(entries):
        is_last = index == len(entries) - 1

        branch = "└── " if is_last else "├── "
        lines.append(f"{prefix}{branch}{entry.name}")

        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(generate_tree(entry, prefix + extension))

    return lines


def main() -> None:
    """Generate the project map."""
    tree = generate_tree(SOURCE_ROOT)

    content = "\n".join(
        [
            "# Sonos Rescue Project Map",
            "",
            "## File Structure",
            "",
            "```text",
            SOURCE_ROOT.name,
            *tree,
            "```",
            "",
        ]
    )

    OUTPUT_FILE.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
