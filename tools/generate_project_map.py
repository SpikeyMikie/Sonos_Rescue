import ast
from collections.abc import Sequence
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
}
EXCLUDED_SUFFIXES = {".png"}


def is_excluded(entry: Path) -> bool:
    """Return whether a file or directory should be omitted from the map."""
    return entry.name in EXCLUDED_NAMES or entry.suffix.lower() in EXCLUDED_SUFFIXES


def append_ast_details(nodes: Sequence[ast.AST], prefix: str, lines: list[str]) -> None:
    """Append AST definitions, nesting class methods beneath their classes."""
    details: list[tuple[str, Sequence[ast.AST]]] = []
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            class_children = [
                child
                for child in node.body
                if isinstance(
                    child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                )
            ]
            details.append((f"class {node.name}", class_children))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            details.append((f"def {node.name}()", []))

    for detail_index, (detail, nested_nodes) in enumerate(details):
        is_last = detail_index == len(details) - 1
        detail_branch = "└── " if is_last else "├── "
        lines.append(f"{prefix}{detail_branch}{detail}")
        if nested_nodes:
            child_prefix = prefix + ("    " if is_last else "│   ")
            append_ast_details(nested_nodes, child_prefix, lines)


def generate_tree(path: Path, prefix: str = "") -> list[str]:
    """Generate a tree-style representation of a directory."""
    entries = sorted(
        (entry for entry in path.iterdir() if not is_excluded(entry)),
        key=lambda item: (item.is_file(), item.name.lower()),
    )

    lines: list[str] = []

    for index, entry in enumerate(entries):
        is_last = index == len(entries) - 1
        branch = "└── " if is_last else "├── "
        line = f"{prefix}{branch}{entry.name}"
        lines.append(line)

        if entry.suffix == ".py":
            source = entry.read_text(encoding="utf-8")
            tree = ast.parse(source)
            docstring = ast.get_docstring(tree)
            if docstring:
                doc_prefix = prefix + ("    " if is_last else "│   ")
                lines.append(f"{doc_prefix}├── doc: {docstring}")
            detail_prefix = prefix + ("    " if is_last else "│   ")
            append_ast_details(tree.body, detail_prefix, lines)

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

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Project map written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
