from __future__ import annotations

import pytest

from graphrender import GraphRender
from graphrender.profile import (
    css_class_token,
    render_kwargs_from_profile_bundle,
    resolve_profile_render_bundle,
)


def _profile_bundle(render_css: str = '.node.router > rect { fill: red; }') -> dict:
    return {
        'schemaVersion': 'v1',
        'profileId': 'runtime',
        'profileVersion': 4,
        'checksum': 'abc123',
        'renderCss': render_css,
    }


def test_css_class_token_normalizes_values_for_css_selectors() -> None:
    assert css_class_token('Router') == 'router'
    assert css_class_token('100G') == 'type-100g'
    assert css_class_token('core edge') == 'core-edge'
    assert css_class_token('') == 'type-unknown'


def test_resolve_profile_render_bundle_validates_required_fields() -> None:
    resolved = resolve_profile_render_bundle(_profile_bundle())

    assert resolved.profile_id == 'runtime'
    assert resolved.profile_version == 4
    assert resolved.checksum == 'abc123'
    assert 'fill: red' in resolved.render_css

    with pytest.raises(ValueError, match="missing required field 'renderCss'"):
        resolve_profile_render_bundle({'profileId': 'x', 'profileVersion': 1, 'checksum': '1'})

    with pytest.raises(ValueError, match="field 'renderCss' must not be empty"):
        resolve_profile_render_bundle(_profile_bundle('   '))


def test_render_kwargs_from_profile_bundle_are_graph_render_ready() -> None:
    kwargs = render_kwargs_from_profile_bundle(_profile_bundle())

    assert kwargs == {
        'theme_css': '.node.router > rect { fill: red; }',
        'embed_theme': True,
        'theme_id': 'default',
    }


def test_graph_render_uses_normalized_type_classes_for_nodes_and_edges() -> None:
    graph = {
        'id': 'root',
        'width': 200,
        'height': 100,
        'children': [
            {
                'id': 'n1',
                'x': 10,
                'y': 10,
                'width': 60,
                'height': 30,
                'type': '100G',
            },
            {
                'id': 'n2',
                'x': 120,
                'y': 10,
                'width': 60,
                'height': 30,
                'type': 'Router Core',
            },
        ],
        'edges': [
            {
                'id': 'e1',
                'type': 'Edge Dependency',
                'sections': [
                    {
                        'startPoint': {'x': 70, 'y': 25},
                        'endPoint': {'x': 120, 'y': 25},
                        'bendPoints': [],
                    }
                ],
            }
        ],
    }

    svg_text = GraphRender(graph, embed_theme=False).to_string(pretty=False)

    assert 'class="node type-100g"' in svg_text
    assert 'class="node router-core"' in svg_text
    assert 'class="edge edge-dependency"' in svg_text
