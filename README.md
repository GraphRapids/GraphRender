# GraphRender

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![CI](https://github.com/Faerkeren/GraphRender/actions/workflows/ci.yml/badge.svg)](https://github.com/Faerkeren/GraphRender/actions/workflows/ci.yml)
[![Tests](https://github.com/Faerkeren/GraphRender/actions/workflows/test.yml/badge.svg)](https://github.com/Faerkeren/GraphRender/actions/workflows/test.yml)
[![Secret Scan](https://github.com/Faerkeren/GraphRender/actions/workflows/gitleaks.yml/badge.svg)](https://github.com/Faerkeren/GraphRender/actions/workflows/gitleaks.yml)

GraphRender converts laid-out ELK JSON into styled SVG diagrams.

It is intended for pipelines where layout is already computed and rendering must be deterministic, inspectable, and themeable.

## Features

- Render nodes, ports, edges, and labels from ELK layout output
- Support nested/compound graphs with coordinate normalization
- Style output with embedded CSS or custom CSS/SCSS/SASS themes
- Profile-bundle adapter for `renderCss` bundle payloads
- Optional Iconify icon rendering with persistent disk cache
- Pretty-formatted SVG output for readable diffs

## Requirements

- Python `>=3.10`
- `svg.py>=1.0`
- Optional: Dart Sass CLI (`sass`) for `.scss` / `.sass` themes

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Quick Start

```bash
# Render an ELK JSON file
python main.py examples/input.json -o output/output.svg

# Render with a custom theme
python main.py examples/input.json --theme themes/theme.scss -o output/custom-theme.svg

# Disable embedded theme
python main.py examples/input.json --no-theme -o output/no-theme.svg
```

## CLI Reference

```bash
python main.py <layout.json> [-o output.svg] [--theme theme.css|theme.scss|theme.sass] [--no-theme]
```

- `<layout.json>`: ELK output JSON with resolved coordinates
- `-o`, `--output`: output SVG path (default: `<input_stem>.svg`)
- `--theme`: CSS/SCSS/SASS theme file path
- `--no-theme`: disable embedded theme block in output SVG

## Python API

```python
from graphrender import GraphRender

renderer = GraphRender.from_file(
    "examples/input.json",
    embed_theme=True,
    theme_css=None,
)

renderer.write("output/output.svg")
svg_text = renderer.to_string()

# Profile-bundle-driven render configuration
profile_bundle = {
    "profileId": "runtime",
    "profileVersion": 1,
    "checksum": "abc",
    "renderCss": ".node.router > rect { fill: #334455; }",
}
renderer = GraphRender.from_profile_bundle(
    graph={"id": "root", "children": [], "edges": []},
    profile_bundle=profile_bundle,
)
```

Main constructor options:

- `padding`
- `node_style`
- `port_style`
- `edge_style`
- `font_size`
- `embed_theme`
- `theme_css`

## Profile Adapter + Class Alignment

`graphrender.profile` provides:

- `resolve_profile_render_bundle()`
- `render_kwargs_from_profile_bundle()`
- `css_class_token()`

`css_class_token()` normalizes `node.type`/`edge.type` values into CSS-safe class names, so selectors remain deterministic.

## Input Expectations

GraphRender assumes layout is already done.

Typical input includes:

- root dimensions (`width`, `height`) or resolvable node extents
- `children` with node geometry (`x`, `y`, `width`, `height`)
- `ports` and optional `labels`
- `edges` with routed `sections` (or source/target ports for fallback)

## Icon Support and Cache

If a node has an `icon` value (Iconify name like `mdi:router`), GraphRender fetches icon SVGs and reuses them via `<defs>/<use>`.

Caching behavior:

- In-memory cache for the current render process
- Persistent disk cache across runs
- Corrupted cache entries are auto-healed (deleted and fetched again)

Configure cache location with:

```bash
export GRAPHRENDER_ICON_CACHE_DIR=/path/to/cache
```

If unset, GraphRender uses platform cache locations (for example `~/.cache/graphrender/icons` on Linux/macOS).

Set `GRAPHRENDER_ICON_CACHE_DIR` to an empty string to disable disk caching.

## Theming Notes

- `.css` themes are embedded directly
- `.scss` / `.sass` themes are compiled with the `sass` CLI
- Theme sources:
  - `themes/_variables.scss`
  - `themes/theme.scss`
  - `src/graphrender/resources/default_theme.css`

## Troubleshooting

### `SCSS/SASS theme compilation requires the sass CLI in PATH`

Install Dart Sass and ensure `sass` is available in your shell.

### Missing icons

- Confirm outbound access to Iconify API
- Check cache directory permissions
- Retry rendering; invalid cache entries are automatically repaired

### `python` command fails with syntax errors

Use `python3` explicitly.

## Development

```bash
python -m pytest -q
python -m py_compile main.py src/graphrender/__init__.py src/graphrender/graphrender.py src/graphrender/resources/__init__.py
python main.py examples/input.json -o /tmp/graphrender-check.svg
```

## Project Layout

```text
main.py                               # CLI entrypoint
src/graphrender/graphrender.py        # Core renderer
src/graphrender/resources/            # Bundled theme/resources
themes/                               # SCSS theme source
examples/                             # Example ELK input
tests/                                # Pytest suite
```

## Governance and Community

- Security policy: `SECURITY.md`
- Contribution guide: `CONTRIBUTING.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- Changelog: `CHANGELOG.md`
- Release process: `RELEASE.md`

## Automation

- CI build and sanity checks: `.github/workflows/ci.yml`
- Test matrix + coverage gate: `.github/workflows/test.yml`
- Secret scanning (gitleaks): `.github/workflows/gitleaks.yml`
- Tagged releases: `.github/workflows/release.yml`
- Dependency updates: `.github/dependabot.yml`

## Acknowledgements

- Eclipse Layout Kernel (ELK) for graph layout modeling and options
- `svg.py` for Python SVG element construction
- Iconify for icon assets and API-based SVG retrieval
- Dart Sass for SCSS/SASS theme compilation support

## Third-Party Notices

See `THIRD_PARTY_NOTICES.md` for dependency, service, and icon-set license notices.

## License

GraphRender is licensed under Apache License 2.0. See `LICENSE`.
