from __future__ import annotations

import re
from pathlib import Path

from tools.generate_project_docs import (
    ClassRelationship,
    discover_class_relationships,
    generate_app_overview,
    generate_class_diagram,
    generate_dependency_diagram,
    generate_diagrams,
    scan_project,
)


def _write(root: Path, relative_path: str, content: str = "") -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_resolves_relative_imports_and_class_relationships(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src" / "demo"
    _write(source_root, "__init__.py")
    _write(source_root, "ui/__init__.py")
    _write(source_root, "managers/__init__.py")
    _write(source_root, "ui/card.py", "class Card:\n    pass\n")
    _write(source_root, "managers/speakers.py", "class SpeakerManager:\n    pass\n")
    _write(
        source_root,
        "ui/panel.py",
        """from typing import Protocol
from .card import Card
from ..managers.speakers import SpeakerManager

class PanelProtocol(Protocol):
    pass

class Panel:
    def __init__(self, manager: SpeakerManager) -> None:
        self.manager = manager
        self.card = Card()

class PanelImpl(PanelProtocol):
    pass
""",
    )

    project = scan_project(source_root, "demo")
    panel = project.modules["demo.ui.panel"]

    assert panel.internal_imports == {
        "demo.managers.speakers",
        "demo.ui.card",
    }
    relationships = discover_class_relationships(project)
    assert any(
        relationship.source == "demo.ui.panel.PanelImpl"
        and relationship.target == "demo.ui.panel.PanelProtocol"
        and relationship.kind == "realisation"
        for relationship in relationships
    )
    assert any(
        relationship.source == "demo.ui.panel.Panel"
        and relationship.target == "demo.ui.card.Card"
        and relationship.kind == "composition"
        for relationship in relationships
    )
    assert any(
        relationship.source == "demo.ui.panel.Panel"
        and relationship.target == "demo.managers.speakers.SpeakerManager"
        and relationship.kind == "association"
        for relationship in relationships
    )


def test_dependency_diagram_uses_unique_canonical_module_nodes() -> None:
    source_root = Path(__file__).parents[2] / "src" / "sonos_rescue"
    project = scan_project(source_root)
    diagram = generate_dependency_diagram(project)

    labels = re.findall(r'\["([^"]+)"\]', diagram)
    assert len(labels) == len(set(labels))
    assert set(labels) == set(project.modules)
    assert "sonos_rescue.ui.artwork_panel" in labels
    assert "sonos_rescue.managers.artwork_manager" in labels
    assert "ui_artwork_panel" not in labels


def test_class_diagram_shows_relationship_types() -> None:
    source_root = Path(__file__).parents[2] / "src" / "sonos_rescue"
    project = scan_project(source_root)
    diagram = generate_class_diagram(project)

    assert "<|--" in diagram
    assert "*--" in diagram
    assert "..>" in diagram

    relationships = discover_class_relationships(project)
    server = "sonos_rescue.services.local_music_server.LocalMusicServer"
    handler = "sonos_rescue.services.local_music_server.QuietHTTPRequestHandler"
    port_error = "sonos_rescue.services.local_music_server.PortInUseError"
    assert ClassRelationship(server, handler, "dependency") in relationships
    assert ClassRelationship(server, port_error, "dependency") in relationships
    assert ClassRelationship(server, handler, "inheritance") not in relationships
    assert ClassRelationship(server, port_error, "inheritance") not in relationships


def test_diagrams_include_requested_mermaid_configurations() -> None:
    source_root = Path(__file__).parents[2] / "src" / "sonos_rescue"
    diagrams = generate_diagrams(scan_project(source_root))

    expected = {
        "app-overview": "    layout: elk\n    theme: redux-dark-color",
        "architecture": "    layout: elk\n    theme: neo-dark",
        "ui-architecture": "    layout: elk\n    theme: redux-dark-color",
        "class-relationships": (
            "    layout: elk\n    theme: redux-dark-color\n"
            "    class:\n        hideEmptyMembersBox: true"
        ),
        "dependencies": "    theme: neo-dark\n    layout: elk",
    }
    for name, config in expected.items():
        assert diagrams[name].startswith(f"---\nconfig:\n{config}\n---\n")


def test_app_overview_stays_at_component_level() -> None:
    source_root = Path(__file__).parents[2] / "src" / "sonos_rescue"
    diagram = generate_app_overview(scan_project(source_root))

    assert '["MainWindow"]' in diagram
    assert '["LocalMusicServer"]' in diagram
    assert "RainbowBackground" not in diagram
    assert "ScalingImageLabel" not in diagram
