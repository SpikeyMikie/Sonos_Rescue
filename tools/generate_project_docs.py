from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass
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
DIAGRAM_CONFIGS: dict[str, dict[str, str | dict[str, bool]]] = {
    "app-overview": {
        "layout": "elk",
        "theme": "redux-dark-color",
    },
    "architecture": {
        "layout": "elk",
        "theme": "redux-dark-color",
    },
    "ui-architecture": {
        "layout": "elk",
        "theme": "redux-dark-color",
    },
    "class-relationships": {
        "layout": "elk",
        "theme": "redux-dark-color",
        "class": {"hideEmptyMembersBox": True},
    },
    "dependencies": {
        "theme": "neo-dark",
        "layout": "elk",
    },
}


@dataclass
class ProjectModule:
    """AST and import data for one canonical project module."""

    name: str
    path: Path
    tree: ast.Module
    internal_imports: set[str]
    external_imports: set[str]
    bindings: dict[str, str]


@dataclass(frozen=True)
class ProjectModel:
    """The single scanned source model used by every generated view."""

    source_root: Path
    package: str
    modules: dict[str, ProjectModule]

    @property
    def modules_by_path(self) -> dict[Path, ProjectModule]:
        return {module.path.resolve(): module for module in self.modules.values()}

    @property
    def classes(self) -> dict[str, tuple[ProjectModule, ast.ClassDef]]:
        return {
            f"{module.name}.{node.name}": (module, node)
            for module in self.modules.values()
            for node in module.tree.body
            if isinstance(node, ast.ClassDef)
        }


@dataclass(frozen=True, order=True)
class ClassRelationship:
    """A relationship discovered between two project classes."""

    source: str
    target: str
    kind: str


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


def _format_parameter(argument: ast.arg, default: ast.expr | None = None) -> str:
    parameter = argument.arg
    if argument.annotation is not None:
        parameter += f": {ast.unparse(argument.annotation)}"
    if default is not None:
        parameter += f" = {ast.unparse(default)}"
    return parameter


def format_function_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    """Return a readable function signature from an AST function node."""
    arguments = node.args
    positional = [*arguments.posonlyargs, *arguments.args]
    defaults = [None] * (len(positional) - len(arguments.defaults)) + list(
        arguments.defaults
    )
    parameters = [
        _format_parameter(argument, default)
        for argument, default in zip(positional, defaults)
    ]
    if arguments.posonlyargs:
        parameters.insert(len(arguments.posonlyargs), "/")
    if arguments.vararg is not None:
        parameters.append(f"*{_format_parameter(arguments.vararg)}")
    elif arguments.kwonlyargs:
        parameters.append("*")
    parameters.extend(
        _format_parameter(argument, default)
        for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults)
    )
    if arguments.kwarg is not None:
        parameters.append(f"**{_format_parameter(arguments.kwarg)}")
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{prefix}def {node.name}({', '.join(parameters)}){returns}"


def _append_function_metadata(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    prefix: str,
    lines: list[str],
) -> None:
    metadata: list[tuple[str, Sequence[ast.AST]]] = []
    if node.decorator_list:
        decorators = ", ".join(f"@{ast.unparse(item)}" for item in node.decorator_list)
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
        child_prefix = prefix + ("    " if is_last else "│   ")
        if isinstance(node, ast.ClassDef):
            lines.append(f"{prefix}{branch}class {node.name}")
            metadata: list[tuple[str, Sequence[ast.AST]]] = []
            docstring = ast.get_docstring(node, clean=True)
            if docstring:
                metadata.append((f"doc: {summarize_docstring(docstring)}", []))
            if node.bases:
                metadata.append(
                    (
                        "bases: " + ", ".join(ast.unparse(base) for base in node.bases),
                        [],
                    )
                )
            if node.decorator_list:
                metadata.append(
                    (
                        "decorators: "
                        + ", ".join(
                            f"@{ast.unparse(item)}" for item in node.decorator_list
                        ),
                        [],
                    )
                )
            methods = [
                item
                for item in node.body
                if isinstance(
                    item, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                )
            ]
            if methods:
                metadata.append(("methods", methods))
            append_children(metadata, child_prefix, lines)
        else:
            lines.append(
                f"{prefix}{branch}{method_visibility(node.name)} "
                f"{format_function_signature(node)}"
            )
            if node.decorator_list or ast.get_docstring(node, clean=True):
                _append_function_metadata(node, child_prefix, lines)


def canonical_module_name(path: Path, source_root: Path, package: str) -> str:
    """Map a Python file to its one canonical importable module name."""
    parts = list(path.relative_to(source_root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join((package, *parts))


def _resolve_relative_import(
    module_name: str,
    path: Path,
    level: int,
    imported_module: str | None,
    package: str,
) -> str:
    if level == 0:
        return imported_module or ""
    current = module_name.split(".")
    if path.name != "__init__.py":
        current.pop()
    parts = current[: max(0, len(current) - level + 1)]
    if imported_module:
        parts.extend(imported_module.split("."))
    return ".".join(parts) or package


def scan_project(source_root: Path, package: str = PROJECT_PACKAGE) -> ProjectModel:
    """Parse modules once, resolving absolute and relative imports canonically."""
    source_root = source_root.resolve()
    paths = sorted(
        (path for path in source_root.rglob("*.py") if not is_excluded(path)),
        key=lambda path: path.as_posix(),
    )
    trees = {path: ast.parse(path.read_text(encoding="utf-8")) for path in paths}
    names = {path: canonical_module_name(path, source_root, package) for path in paths}
    known_modules = set(names.values())
    modules: dict[str, ProjectModule] = {}

    for path in paths:
        name = names[path]
        module = ProjectModule(name, path, trees[path], set(), set(), {})
        for node in ast.walk(module.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bound_name = alias.asname or alias.name.split(".")[0]
                    module.bindings[bound_name] = (
                        alias.name if alias.asname else bound_name
                    )
                    if alias.name in known_modules:
                        module.internal_imports.add(alias.name)
                    else:
                        module.external_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                base = _resolve_relative_import(
                    name, path, node.level, node.module, package
                )
                children = {
                    f"{base}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*" and f"{base}.{alias.name}" in known_modules
                }
                if children:
                    module.internal_imports.update(children)
                elif base in known_modules:
                    module.internal_imports.add(base)
                elif base:
                    module.external_imports.add(base)

                for alias in node.names:
                    if alias.name == "*":
                        continue
                    bound_name = alias.asname or alias.name
                    child_name = f"{base}.{alias.name}" if base else alias.name
                    module.bindings[bound_name] = (
                        child_name if child_name in known_modules else child_name
                    )
        modules[name] = module
    return ProjectModel(source_root, package, modules)


def generate_tree(path: Path, project: ProjectModel, prefix: str = "") -> list[str]:
    """Generate the existing detailed source tree from the shared AST model."""
    entries = sorted(
        (entry for entry in path.iterdir() if not is_excluded(entry)),
        key=lambda item: (item.is_file(), item.name.lower()),
    )
    lines: list[str] = []
    modules_by_path = project.modules_by_path
    for index, entry in enumerate(entries):
        is_last = index == len(entries) - 1
        branch = "└── " if is_last else "├── "
        lines.append(f"{prefix}{branch}{entry.name}")
        child_prefix = prefix + ("    " if is_last else "│   ")
        if entry.suffix == ".py":
            module = modules_by_path[entry.resolve()]
            docstring = ast.get_docstring(module.tree, clean=True)
            if docstring:
                lines.append(f"{child_prefix}├── doc: {summarize_docstring(docstring)}")
            append_ast_details(module.tree.body, child_prefix, lines)
        elif entry.is_dir():
            lines.extend(generate_tree(entry, project, child_prefix))
    return lines


def _module_id(module_name: str) -> str:
    """Create a stable Mermaid ID that preserves canonical module identity."""
    return "module_" + "_".join(
        part.replace("_", "__") for part in module_name.split(".")
    )


def _class_id(class_name: str) -> str:
    return "class_" + _module_id(class_name)


def _class_reference(
    expression: ast.expr,
    module: ProjectModule,
    classes: dict[str, tuple[ProjectModule, ast.ClassDef]],
) -> str | None:
    """Resolve local or imported class names against the project class index."""
    parts: list[str] = []
    current = expression
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    parts.reverse()
    binding = module.bindings.get(parts[0])
    reference = (
        ".".join((binding, *parts[1:]))
        if binding
        else (f"{module.name}." + ".".join(parts))
    )
    candidates = [reference]
    if binding:
        candidates.append(binding)
    return next((candidate for candidate in candidates if candidate in classes), None)


def _is_protocol(class_node: ast.ClassDef) -> bool:
    return any(
        ast.unparse(base).split(".")[-1] == "Protocol" for base in class_node.bases
    )


def _annotation_class_references(
    annotation: ast.expr,
    module: ProjectModule,
    classes: dict[str, tuple[ProjectModule, ast.ClassDef]],
) -> set[str]:
    """Resolve project classes referenced in an annotation, including strings."""
    references: set[str] = set()

    def visit(expression: ast.expr) -> None:
        if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
            try:
                forward_expression = ast.parse(expression.value, mode="eval").body
            except SyntaxError:
                return
            visit(forward_expression)
            return

        if isinstance(expression, (ast.Name, ast.Attribute)):
            reference = _class_reference(expression, module, classes)
            if reference:
                references.add(reference)

        for child in ast.iter_child_nodes(expression):
            visit(child)

    visit(annotation)
    return references


def discover_class_relationships(project: ProjectModel) -> set[ClassRelationship]:
    """Discover class relationships from annotations, bases, and construction."""
    classes = project.classes
    relationships: set[ClassRelationship] = set()

    for qualified_name, (module, class_node) in classes.items():
        # Explicit base classes represent inheritance or protocol realisation.
        for base in class_node.bases:
            target = _class_reference(base, module, classes)
            if target:
                kind = (
                    "realisation" if _is_protocol(classes[target][1]) else "inheritance"
                )
                relationships.add(ClassRelationship(qualified_name, target, kind))

        # Annotations represent dependencies; annotated fields represent associations.
        class_level_annotations = {id(node) for node in class_node.body}
        for node in ast.walk(class_node):
            annotations: list[ast.expr] = []

            if isinstance(node, ast.arg) and node.annotation is not None:
                annotations.append(node.annotation)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns is not None:
                    annotations.append(node.returns)
            elif isinstance(node, ast.AnnAssign):
                annotations.append(node.annotation)

            if not annotations:
                continue

            is_attribute = isinstance(node, ast.AnnAssign) and (
                id(node) in class_level_annotations
                or (
                    isinstance(node.target, ast.Attribute)
                    and isinstance(node.target.value, ast.Name)
                    and node.target.value.id == "self"
                )
            )
            kind = "association" if is_attribute else "dependency"

            for annotation in annotations:
                for target in _annotation_class_references(annotation, module, classes):
                    if target != qualified_name:
                        relationships.add(
                            ClassRelationship(qualified_name, target, kind)
                        )

        # Preserve constructor-based composition and typed self-attribute detection.
        for method in (
            item
            for item in class_node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            args = [
                *method.args.posonlyargs,
                *method.args.args,
                *method.args.kwonlyargs,
            ]
            argument_types: dict[str, str | None] = {
                arg.arg: next(
                    iter(_annotation_class_references(arg.annotation, module, classes)),
                    None,
                )
                for arg in args
                if arg.annotation is not None
            }

            for arg in (method.args.vararg, method.args.kwarg):
                if arg and arg.annotation:
                    argument_types[arg.arg] = next(
                        iter(
                            _annotation_class_references(
                                arg.annotation, module, classes
                            )
                        ),
                        None,
                    )

            for node in ast.walk(method):
                if isinstance(node, ast.Call):
                    passed_classes = [
                        *node.args,
                        *(keyword.value for keyword in node.keywords),
                    ]
                    for expression in passed_classes:
                        target = _class_reference(expression, module, classes)
                        if target and target != qualified_name:
                            relationships.add(
                                ClassRelationship(qualified_name, target, "dependency")
                            )

                if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                    target = _class_reference(node.exc.func, module, classes)
                    if target and target != qualified_name:
                        relationships.add(
                            ClassRelationship(qualified_name, target, "dependency")
                        )

                value: ast.expr | None = None
                targets: list[ast.expr] = []
                if isinstance(node, ast.Assign):
                    value, targets = node.value, node.targets
                elif isinstance(node, ast.AnnAssign):
                    value, targets = node.value, [node.target]

                for target in targets:
                    is_self_attribute = (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    )
                    if (
                        value is not None
                        and is_self_attribute
                        and isinstance(value, ast.Name)
                    ):
                        related = argument_types.get(value.id)
                        if related:
                            relationships.add(
                                ClassRelationship(
                                    qualified_name, related, "association"
                                )
                            )

                if isinstance(value, ast.Call):
                    constructed = _class_reference(value.func, module, classes)
                    if constructed and constructed != qualified_name:
                        owns_member = any(
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                            for target in targets
                        )
                        kind = (
                            "composition"
                            if method.name == "__init__" or owns_member
                            else "dependency"
                        )
                        relationships.add(
                            ClassRelationship(qualified_name, constructed, kind)
                        )

    priority = {
        "dependency": 0,
        "association": 1,
        "composition": 2,
        "inheritance": 3,
        "realisation": 4,
    }
    strongest: dict[tuple[str, str], ClassRelationship] = {}
    for relationship in relationships:
        key = (relationship.source, relationship.target)
        existing = strongest.get(key)
        if existing is None or priority[relationship.kind] > priority[existing.kind]:
            strongest[key] = relationship

    return set(strongest.values())


PRIMARY_COMPONENTS = {
    "sonos_rescue.ui.main_window": "MainWindow",
    "sonos_rescue.ui.rooms_panel": "RoomsPanel",
    "sonos_rescue.ui.room_card": "RoomCard",
    "sonos_rescue.ui.artwork_panel": "ArtworkPanel",
    "sonos_rescue.ui.playlist_panel": "PlaylistPanel",
    "sonos_rescue.ui.transport_controls": "TransportControls",
    "sonos_rescue.ui.widgets.rainbow_background": "RainbowBackground",
    "sonos_rescue.ui.widgets.rainbow_frame": "RainbowFrame",
    "sonos_rescue.ui.widgets.scaling_image_label": "ScalingImageLabel",
    "sonos_rescue.managers.speaker_manager": "SpeakerManager",
    "sonos_rescue.managers.playback_controller": "PlaybackController",
    "sonos_rescue.managers.playback_poller": "PlaybackPoller",
    "sonos_rescue.managers.artwork_manager": "ArtworkManager",
    "sonos_rescue.services.local_music_server": "LocalMusicServer",
    "sonos_rescue.database.database": "ArtworkDatabase",
}


def _components(project: ProjectModel) -> dict[str, str]:
    classes = project.classes
    return {
        module: name
        for module, name in PRIMARY_COMPONENTS.items()
        if f"{module}.{name}" in classes
    }


def _layer(module_name: str) -> str:
    parts = module_name.split(".")
    return parts[1] if len(parts) > 1 else "application"


def generate_app_overview(project: ProjectModel) -> str:
    """Generate a compact diagram containing primary components only."""
    components = {
        module: component
        for module, component in _components(project).items()
        if ".widgets." not in module
    }
    lines = ["flowchart TD", ""]
    for layer in ("ui", "managers", "services", "database"):
        modules = [name for name in sorted(components) if _layer(name) == layer]
        if not modules:
            continue
        label = "UI" if layer == "ui" else layer.title()
        lines.append(f'    subgraph {layer}["{label}"]')
        for module in modules:
            lines.append(f'        {_module_id(module)}["{components[module]}"]')
        lines.extend(["    end", ""])
    for module in sorted(components):
        for dependency in sorted(project.modules[module].internal_imports):
            if dependency in components:
                lines.append(f"    {_module_id(module)} --> {_module_id(dependency)}")
    return "\n".join([*lines, ""])


def generate_architecture_diagram(project: ProjectModel) -> str:
    """Generate the layered application view and source-backed system links."""
    components = {
        module: component
        for module, component in _components(project).items()
        if ".widgets." not in module
    }
    lines = ["flowchart TD", ""]
    for layer in ("ui", "managers", "services", "database"):
        modules = [name for name in sorted(components) if _layer(name) == layer]
        if modules:
            label = "UI" if layer == "ui" else layer.title()
            lines.append(f'    subgraph {layer}["{label}"]')
            for module in modules:
                lines.append(f'        {_module_id(module)}["{components[module]}"]')
            lines.extend(["    end", ""])

    external_labels = {
        "PyQt6": "PyQt6",
        "soco": "SoCo / Sonos",
        "sqlite3": "SQLite",
        "http": "Local HTTP server",
        "urllib": "HTTP",
        "pathlib": "Filesystem",
        "socket": "Network",
    }
    external_roots = {
        imported.split(".")[0]
        for name in components
        for imported in project.modules[name].external_imports
        if imported.split(".")[0] in external_labels
    }
    if external_roots:
        lines.append('    subgraph external["External systems"]')
        for root in sorted(external_roots):
            lines.append(f'        external_{root}["{external_labels[root]}"]')
        lines.extend(["    end", ""])

    for module in sorted(components):
        for dependency in sorted(project.modules[module].internal_imports):
            if dependency in components:
                lines.append(f"    {_module_id(module)} --> {_module_id(dependency)}")
        imported_roots = {
            imported.split(".")[0]
            for imported in project.modules[module].external_imports
        }
        for root in sorted(imported_roots):
            if root in external_roots:
                lines.append(f"    {_module_id(module)} --> external_{root}")
    service = "sonos_rescue.services.local_music_server"
    if service in components and "soco" in external_roots:
        lines.append(f"    {_module_id(service)} -->|streams files to| external_soco")
    return "\n".join([*lines, ""])


def generate_ui_diagram(project: ProjectModel) -> str:
    """Generate the GUI structure from UI classes and AST-discovered relations."""
    classes = project.classes
    ui_classes = {
        name: item
        for name, item in classes.items()
        if item[0].name.startswith("sonos_rescue.ui.")
    }
    relationships = discover_class_relationships(project)
    lines = ["flowchart TD", ""]
    groups = {
        "ui": [
            name
            for name, (module, _) in ui_classes.items()
            if ".widgets." not in module.name
        ],
        "widgets": [
            name
            for name, (module, _) in ui_classes.items()
            if ".widgets." in module.name
        ],
    }
    for group, names in groups.items():
        if names:
            lines.append(f'    subgraph {group}["{group.title()}"]')
            for name in sorted(names):
                lines.append(f'        {_class_id(name)}["{name.rsplit(".", 1)[-1]}"]')
            lines.extend(["    end", ""])
    for relationship in sorted(relationships):
        if relationship.source in ui_classes and relationship.target in ui_classes:
            lines.append(
                f"    {_class_id(relationship.source)} --> "
                f"{_class_id(relationship.target)}"
            )
    return "\n".join([*lines, ""])


def generate_class_diagram(project: ProjectModel) -> str:
    """Generate class-level inheritance and composition relationships."""
    classes = project.classes
    relationships = discover_class_relationships(project)
    lines = ["classDiagram"]
    for name, (_, node) in sorted(classes.items()):
        lines.append(f'    class {_class_id(name)}["{node.name}"]')

    external_bases: set[str] = set()
    for name, (module, node) in classes.items():
        for base in node.bases:
            if _class_reference(base, module, classes) is None:
                short_name = ast.unparse(base).split(".")[-1]
                if short_name != "Protocol":
                    external_bases.add(short_name)
    for name in sorted(external_bases):
        lines.append(f'    class external_{_module_id(name)}["{name}"]')

    arrows = {
        "inheritance": "<|--",
        "realisation": "<|..",
        "composition": "*--",
        "association": "-->",
        "dependency": "..>",
    }
    for relationship in sorted(relationships):
        if relationship.kind in {"inheritance", "realisation"}:
            source, target = relationship.target, relationship.source
        else:
            source, target = relationship.source, relationship.target
        lines.append(
            f"    {_class_id(source)} {arrows[relationship.kind]} {_class_id(target)}"
        )
    for name, (module, node) in sorted(classes.items()):
        for base in node.bases:
            if _class_reference(base, module, classes) is None:
                short_name = ast.unparse(base).split(".")[-1]
                if short_name != "Protocol":
                    lines.append(
                        f"    external_{_module_id(short_name)} <|-- {_class_id(name)}"
                    )
    return "\n".join([*lines, ""])


def generate_dependency_diagram(project: ProjectModel) -> str:
    """Generate the module import graph with canonical module names."""
    lines = ["flowchart LR"]
    for name in sorted(project.modules):
        lines.append(f'    {_module_id(name)}["{name}"]')
    for name in sorted(project.modules):
        for dependency in sorted(project.modules[name].internal_imports):
            lines.append(f"    {_module_id(name)} --> {_module_id(dependency)}")
    return "\n".join([*lines, ""])


def generate_diagrams(
    project: ProjectModel, *, markdown_compatible: bool = False
) -> dict[str, str]:
    """Generate diagram sources with their per-diagram Mermaid configuration."""
    generators = {
        "app-overview": generate_app_overview,
        "architecture": generate_architecture_diagram,
        "ui-architecture": generate_ui_diagram,
        "class-relationships": generate_class_diagram,
        "dependencies": generate_dependency_diagram,
    }
    diagrams: dict[str, str] = {}
    for name, generator in generators.items():
        config = DIAGRAM_CONFIGS[name].copy()
        if markdown_compatible:
            config.pop("layout", None)
        config_lines = ["---", "config:"]
        for key, value in config.items():
            if isinstance(value, dict):
                config_lines.append(f"  {key}:")
                config_lines.extend(
                    f"    {nested_key}: {str(nested_value).lower()}"
                    for nested_key, nested_value in value.items()
                )
            else:
                config_lines.append(f"  {key}: {value}")
        config_lines.append("---")
        diagrams[name] = "\n".join([*config_lines, generator(project)])
    return diagrams


def _module_summary(module: ProjectModule) -> str:
    docstring = ast.get_docstring(module.tree, clean=True)
    if docstring:
        return summarize_docstring(docstring)
    primary_class = PRIMARY_COMPONENTS.get(module.name)
    if primary_class:
        for node in module.tree.body:
            if isinstance(node, ast.ClassDef) and node.name == primary_class:
                docstring = ast.get_docstring(node, clean=True)
                if docstring:
                    return summarize_docstring(docstring)
                return ""
    for node in module.tree.body:
        if isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node, clean=True)
            if docstring:
                return summarize_docstring(docstring)
    return ""


def _render_layer(project: ProjectModel, layer: str) -> list[str]:
    components = _components(project)
    lines: list[str] = []
    for module_name in sorted(components):
        if _layer(module_name) != layer:
            continue
        description = _module_summary(project.modules[module_name])
        suffix = f" — {description}" if description else ""
        lines.append(f"- `{module_name}` (`{components[module_name]}`){suffix}")
    return lines or ["- No components found."]


def generate_architecture_markdown(
    project: ProjectModel, diagrams: dict[str, str]
) -> str:
    """Build the architecture guide from model summaries and current design."""
    utility_modules = [
        module
        for module in sorted(project.modules.values(), key=lambda item: item.name)
        if _layer(module.name) == "utils"
    ]
    sections = [
        "# Architecture",
        "",
        "> Generated from the Python source tree by `tools/generate_project_docs.py`.",
        "",
        "## Overview",
        "",
        "Sonos Rescue is a PyQt6 desktop controller. Its UI coordinates speaker "
        "discovery and playback managers, uses a local HTTP service to expose "
        "selected music files to Sonos devices, and caches artwork in SQLite.",
        "",
        "## Application Layers",
        "",
        "### UI Layer",
        "",
        *_render_layer(project, "ui"),
        "",
        "### Manager Layer",
        "",
        *_render_layer(project, "managers"),
        "",
        "### Service Layer",
        "",
        *_render_layer(project, "services"),
        "",
        "### Database Layer",
        "",
        *_render_layer(project, "database"),
        "",
        "### Utility Layer",
        "",
        *[
            (
                f"- `{module.name}` — {_module_summary(module)}"
                if _module_summary(module)
                else f"- `{module.name}`"
            )
            for module in utility_modules
        ],
        "",
        "## Threading Model",
        "",
        "`MainWindow` moves `PlaybackPoller` to a `QThread`. The poller reads "
        "Sonos playback data and fetches artwork away from the GUI thread, then "
        "emits an immutable `NowPlayingUpdate` snapshot through a Qt signal. "
        "`MainWindow.apply_now_playing_update()` applies the snapshot and "
        "updates widgets on the GUI thread. Artwork retrieval returns plain "
        "bytes; creation and display of Qt pixmaps remain in the UI path.",
        "",
        "```text",
        "PlaybackPoller (worker thread)",
        "    → Qt signal carrying NowPlayingUpdate",
        "    → MainWindow.apply_now_playing_update()",
        "    → Qt widgets (GUI thread)",
        "```",
        "",
        "## Artwork Data Flow",
        "",
        "The worker calls `ArtworkManager.resolve_and_fetch_art()` to resolve "
        "the Sonos URL, check the SQLite cache, or fetch and process image "
        "bytes. It carries the immutable `ArtResult` to the GUI in "
        "`NowPlayingUpdate`. `MainWindow.apply_now_playing_update()` checks "
        "the in-memory `QPixmap` cache, creates a pixmap when needed, and "
        "updates the artwork widget on the GUI thread.",
        "",
        "## Local Music Server",
        "",
        "`LocalMusicServer` serves files from its configured directory using a "
        "background HTTP server. The handler is bound to that directory; the "
        "process working directory is not changed. `MainWindow` constructs a "
        "Sonos-accessible URL and asks the selected speaker to play it.",
        "",
        "## Data Flow",
        "",
        "- `SpeakerManager` discovers speakers and emits signals consumed by the UI.",
        "- UI controls delegate playback operations to `PlaybackController`.",
        "- `PlaybackPoller` periodically collects playback and queue state and "
        "publishes an immutable update for the UI.",
        "- `ArtworkManager` coordinates artwork retrieval and its SQLite cache.",
        "",
        "## Regenerating Documentation",
        "",
        "From the repository root, run `python tools/generate_project_docs.py`. "
        "The AST scanner writes the project map, this architecture guide, the "
        "canonical import report, and the five Mermaid source files. Repeated "
        "runs without source changes produce stable output; no SVG files or "
        "source-code changes are generated.",
        "",
        "## Architecture Diagrams",
        "",
    ]
    titles = {
        "app-overview": "App Overview",
        "architecture": "Architecture",
        "ui-architecture": "UI Architecture",
        "class-relationships": "Class Relationships",
        "dependencies": "Dependencies",
    }
    for name, source in diagrams.items():
        sections.extend(
            [
                f"### {titles[name]}",
                "",
                "```mermaid",
                source.rstrip(),
                "```",
                "",
                f"Source: [`diagrams/{name}.mmd`](diagrams/{name}.mmd).",
                "",
            ]
        )
    return "\n".join(sections)


def generate_dependencies_markdown(project: ProjectModel) -> str:
    """Generate the existing import report using canonical module names."""
    lines = ["# Sonos Rescue Dependencies", "", "## Import Dependencies", ""]
    for name in sorted(project.modules):
        module = project.modules[name]
        lines.append(f"### `{name}`")
        if module.internal_imports:
            lines.extend(["", "**internal**"])
            lines.extend(f"- `{item}`" for item in sorted(module.internal_imports))
        if module.external_imports:
            lines.extend(["", "**external**"])
            lines.extend(f"- `{item}`" for item in sorted(module.external_imports))
        lines.append("")
    return "\n".join(lines)


def render_project_map(project: ProjectModel) -> None:
    """Generate all documentation views from one AST-backed project model."""
    docs_dir = PROJECT_ROOT / "docs"
    diagrams_dir = docs_dir / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    diagrams = generate_diagrams(project)
    for name, source in diagrams.items():
        (diagrams_dir / f"{name}.mmd").write_text(source, encoding="utf-8")

    tree = generate_tree(project.source_root, project)
    project_map = "\n".join(
        [
            "# Sonos Rescue Project Map",
            "",
            "## File Structure",
            "",
            "```text",
            project.source_root.name,
            *tree,
            "```",
            "",
        ]
    )
    OUTPUT_FILE.write_text(project_map, encoding="utf-8")
    (docs_dir / "architecture.md").write_text(
        generate_architecture_markdown(
            project, generate_diagrams(project, markdown_compatible=True)
        ),
        encoding="utf-8",
    )
    (docs_dir / "dependencies.md").write_text(
        generate_dependencies_markdown(project), encoding="utf-8"
    )
    print(f"Project documentation written to {docs_dir}")


if __name__ == "__main__":
    render_project_map(scan_project(SOURCE_ROOT))
