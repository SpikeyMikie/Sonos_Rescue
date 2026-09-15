import ast
from collections.abc import Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src" / "sonos_rescue"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "project-map.md"
PROJECT_PACKAGE = "sonos_rescue"

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


def summarize_docstring(docstring: str, limit: int = 130) -> str:
    """Collapse a docstring into a short single-line summary."""
    summary = " ".join(docstring.split())
    return summary if len(summary) <= limit else f"{summary[: limit - 3]}..."


def method_visibility(name: str) -> str:
    """Return the visibility of a method based on its name."""
    if name.startswith("__") and name.endswith("__"):
        return "dunder:"
    if name.startswith("_"):
        return "private:"
    return "public:"


def append_children(
    children: Sequence[tuple[str, Sequence[ast.AST]]],
    prefix: str,
    lines: list[str],
) -> None:
    """Append labelled AST children using tree connectors."""
    for index, (label, nested_nodes) in enumerate(children):
        is_last = index == len(children) - 1
        branch = "└── " if is_last else "├── "
        lines.append(f"{prefix}{branch}{label}")
        if nested_nodes:
            child_prefix = prefix + ("    " if is_last else "│   ")
            append_ast_details(nested_nodes, child_prefix, lines)


def format_annotation(annotation: ast.expr | None) -> str:
    """Return readable source text for an annotation."""
    return ast.unparse(annotation) if annotation is not None else ""


def format_parameter(argument: ast.arg, default: ast.expr | None = None) -> str:
    """Format a parameter name, annotation, and optional default value."""
    parameter = argument.arg
    annotation = format_annotation(argument.annotation)
    if annotation:
        parameter += f": {annotation}"
    if default is not None:
        parameter += f" = {ast.unparse(default)}"
    return parameter


def format_function_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    """Return a readable function signature from an AST function node."""
    arguments = node.args
    positional = [*arguments.posonlyargs, *arguments.args]
    positional_defaults = [None] * (len(positional) - len(arguments.defaults)) + list(
        arguments.defaults
    )
    parameters = [
        format_parameter(argument, default)
        for argument, default in zip(positional, positional_defaults)
    ]
    if arguments.posonlyargs:
        parameters.insert(len(arguments.posonlyargs), "/")

    if arguments.vararg is not None:
        parameters.append(f"*{format_parameter(arguments.vararg)}")
    elif arguments.kwonlyargs:
        parameters.append("*")

    parameters.extend(
        format_parameter(argument, default)
        for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults)
    )
    if arguments.kwarg is not None:
        parameters.append(f"**{format_parameter(arguments.kwarg)}")

    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return_annotation = format_annotation(node.returns)
    return_value = f" -> {return_annotation}" if return_annotation else ""
    return f"{prefix}def {node.name}({', '.join(parameters)}){return_value}"


def append_function_details(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    prefix: str,
    lines: list[str],
) -> None:
    """Append decorators and a docstring beneath a function signature."""
    metadata: list[tuple[str, Sequence[ast.AST]]] = []
    if node.decorator_list:
        decorators = ", ".join(
            f"@{ast.unparse(decorator)}" for decorator in node.decorator_list
        )
        metadata.append((f"decorators: {decorators}", []))
    docstring = ast.get_docstring(node, clean=True)
    if docstring:
        metadata.append((f"doc: {summarize_docstring(docstring)}", []))
    append_children(metadata, prefix, lines)


def append_ast_details(nodes: Sequence[ast.AST], prefix: str, lines: list[str]) -> None:
    """Append AST definitions, nesting class methods beneath their classes."""
    definitions = [
        node
        for node in nodes
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    for index, node in enumerate(definitions):
        is_last = index == len(definitions) - 1
        branch = "└── " if is_last else "├── "
        if isinstance(node, ast.ClassDef):
            lines.append(f"{prefix}{branch}class {node.name}")
            metadata: list[tuple[str, Sequence[ast.AST]]] = []
            docstring = ast.get_docstring(node, clean=True)
            if docstring:
                metadata.append((f"doc: {summarize_docstring(docstring)}", []))
            if node.bases:
                bases = ", ".join(ast.unparse(base) for base in node.bases)
                metadata.append((f"bases: {bases}", []))
            if node.decorator_list:
                decorators = ", ".join(
                    f"@{ast.unparse(decorator)}" for decorator in node.decorator_list
                )
                metadata.append((f"decorators: {decorators}", []))

            class_children = [
                child
                for child in node.body
                if isinstance(
                    child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                )
            ]
            if class_children:
                metadata.append(("methods", class_children))
            if metadata:
                child_prefix = prefix + ("    " if is_last else "│   ")
                append_children(metadata, child_prefix, lines)
        else:
            visibility = method_visibility(node.name)
            lines.append(
                f"{prefix}{branch}{visibility} {format_function_signature(node)}"
            )
            if node.decorator_list or ast.get_docstring(node, clean=True):
                child_prefix = prefix + ("    " if is_last else "│   ")
                append_function_details(node, child_prefix, lines)


def generate_tree(path: Path, prefix: str = "") -> list[str]:
    """Generate a tree-style representation of a directory.

    Args:
        path (Path): The root directory to generate the tree from.
        prefix (str, optional): The prefix for the current level of the tree. Defaults to "".

    Returns:
        list[str]: A list of strings representing the tree structure.
    """
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
            docstring = ast.get_docstring(tree, clean=True)
            if docstring:
                doc_prefix = prefix + ("    " if is_last else "│   ")
                lines.append(f"{doc_prefix}├── doc: {summarize_docstring(docstring)}")
            detail_prefix = prefix + ("    " if is_last else "│   ")
            append_ast_details(tree.body, detail_prefix, lines)

        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(generate_tree(entry, prefix + extension))

    return lines


def project_modules(path: Path) -> set[str]:
    """Return a set of canonical module names available under the source package."""
    modules: set[str] = set()
    for entry in path.rglob("*.py"):
        if is_excluded(entry):
            continue
        relative = entry.relative_to(SOURCE_ROOT).with_suffix("")
        parts = relative.parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts:
            modules.add(".".join((PROJECT_PACKAGE, *parts)))
    return modules


def is_internal_import(name: str, modules: set[str]) -> bool:
    """Return whether an import refers to a module in this project."""
    return name.startswith(PROJECT_PACKAGE) or any(
        module == name or module.endswith(f".{name}") for module in modules
    )


def analyze_dependencies(path: Path) -> dict[str, dict[str, set[str]]]:
    """
    Analyze Python file dependencies within a directory.
    Distinguishes between internal and external imports within the project.
    """
    dependencies: dict[str, dict[str, set[str]]] = {}
    modules = project_modules(SOURCE_ROOT)

    for entry in sorted(path.iterdir(), key=lambda item: item.name.lower()):
        if is_excluded(entry):
            continue
        if entry.is_dir():
            dependencies.update(analyze_dependencies(entry))
        elif entry.suffix == ".py":
            source = entry.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)

            dependencies[str(entry.relative_to(SOURCE_ROOT))] = {
                "internal": {
                    name for name in imports if is_internal_import(name, modules)
                },
                "external": {
                    name for name in imports if not is_internal_import(name, modules)
                },
            }

    return dependencies


def render_dependencies(dependencies: dict[str, dict[str, set[str]]]) -> None:
    """Write dependencies to a separate Markdown file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Sonos Rescue Dependencies", ""]
    for file, imports in dependencies.items():
        sections: list[str] = [f"## {file}"]
        if imports["internal"]:
            sections.extend(["", "**internal**"])
            sections.extend(f"- `{name}`" for name in sorted(imports["internal"]))
        if imports["external"]:
            sections.extend(["", "**external**"])
            sections.extend(f"- `{name}`" for name in sorted(imports["external"]))
        lines.extend(sections)
        lines.append("")

    dependencies_file = OUTPUT_FILE.parent / "dependencies.md"
    dependencies_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Dependencies written to {OUTPUT_FILE.parent / 'dependencies.md'}")


def render_project_map() -> None:
    """Generate the project map."""
    tree = generate_tree(SOURCE_ROOT)
    dependencies = analyze_dependencies(SOURCE_ROOT)
    render_dependencies(dependencies)

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
    render_project_map()
