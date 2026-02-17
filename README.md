# GraphRender

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![CI](https://github.com/Faerkeren/GraphRender/actions/workflows/ci.yml/badge.svg)](https://github.com/Faerkeren/GraphRender/actions/workflows/ci.yml)
[![Tests](https://github.com/Faerkeren/GraphRender/actions/workflows/test.yml/badge.svg)](https://github.com/Faerkeren/GraphRender/actions/workflows/test.yml)
[![Secret Scan](https://github.com/Faerkeren/GraphRender/actions/workflows/gitleaks.yml/badge.svg)](https://github.com/Faerkeren/GraphRender/actions/workflows/gitleaks.yml)

GraphRender converts **laid-out ELK JSON** into styled SVG diagrams.

It is intended for pipelines where layout is already computed (for example by Eclipse Layout Kernel), and you want reliable SVG rendering with optional theming and icon support.

## Features

- Render nodes, ports, edges, and labels from ELK layout output
- Support nested/compound graphs with coordinate normalization
- Style via embedded CSS, or custom CSS/SCSS/SASS themes
- Optional Iconify icon rendering for nodes with persistent disk cache
- Pretty-formatted SVG output for readable diffs and manual inspection

## Requirements

- Python `>=3.10`
- `svg.py >= 1.0`
- Optional: Dart Sass CLI (`sass`) if using `.scss` / `.sass` themes

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

## Quick Start

Render an ELK JSON file:

```bash
python3 main.py examples/input.json -o output/output.svg
```

Use a custom theme:

```bash
python3 main.py examples/input.json --theme themes/theme.scss -o output/custom-theme.svg
```

Use bundled default theme explicitly:

```bash
python3 main.py examples/input.json --theme src/graphrender/resources/default_theme.css -o output/default-theme.svg
```

Disable embedded theme completely:

```bash
python3 main.py examples/input.json --no-theme -o output/no-theme.svg
```

## CLI Reference

```bash
python3 main.py <layout.json> [-o output.svg] [--theme theme.css|theme.scss|theme.sass] [--no-theme]
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
    theme_css=None,  # Or pass your CSS string directly
)

renderer.write("output/output.svg")  # pretty=True by default
svg_text = renderer.to_string()      # pretty formatted XML
```

### Main constructor options

- `padding`: canvas padding around rendered graph
- `node_style`: default node shape style overrides
- `port_style`: default port style overrides
- `edge_style`: default edge style overrides
- `font_size`: fallback label font size
- `embed_theme`: whether to include `<style>` in SVG
- `theme_css`: explicit CSS string to embed

## Input Expectations

GraphRender assumes **layout is already done**.

Typical input includes:

- root graph dimensions (`width`, `height`) or resolvable node extents
- `children` with node geometry (`x`, `y`, `width`, `height`)
- `ports` and optional `labels`
- `edges` with `sections` (or source/target ports for fallback)

## Icon Support and Cache

If a node has an `icon` value (Iconify name like `mdi:router`), GraphRender fetches icon SVGs from Iconify and reuses them via `<defs>/<use>`.

Caching behavior:

- In-memory cache for the current render process
- Persistent disk cache across runs
- Corrupted cache entries are auto-healed (deleted and re-fetched)

Configure cache location with:

```bash
export GRAPHRENDER_ICON_CACHE_DIR=/path/to/cache
```

If unset, defaults to platform cache locations (for example `~/.cache/graphrender/icons` on Linux/macOS).

Set it to an empty string to disable disk caching.

## Theming Notes

- `.css` themes are embedded directly
- `.scss` / `.sass` themes are compiled using the `sass` CLI
- Theme variables and selectors are in:
  - `themes/_variables.scss`
  - `themes/theme.scss`
  - `src/graphrender/resources/default_theme.css` (bundled compiled/default theme)

## Troubleshooting

### `SCSS/SASS theme

compilation requires the sass CLI in PATH`

Install Dart Sass and ensure `sass` is available in your shell.

### Missing icons

- Confirm outbound network access to Iconify API
- Check cache dir permissions
- Retry render; invalid cache entries are auto-repaired

### `python` command fails with syntax errors

Use `python3` explicitly (recommended in all examples).

## Development

Run a local sanity check:

```bash
.venv/bin/python -m py_compile main.py src/graphrender/__init__.py src/graphrender/graphrender.py
.venv/bin/python main.py examples/input.json -o /tmp/graphrender-check.svg
```

## Project Layout

```text
main.py                          # CLI entry point
src/graphrender/graphrender.py   # Core renderer
src/graphrender/resources/       # Bundled theme/assets
themes/                          # SCSS theme source
examples/                        # Example ELK input/output
```

## Acknowledgements

- Eclipse Layout Kernel (ELK) for graph layout modeling and options
- `svg.py` for Python SVG element construction
- Iconify for icon assets and API-based SVG retrieval
- Dart Sass for SCSS/SASS theme compilation support

## Third-Party Notices

See `THIRD_PARTY_NOTICES.md` for dependency, tool, service, and icon set license notices.

## Governance and Community

- Security policy: `SECURITY.md`
- Contribution guide: `CONTRIBUTING.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- Changelog: `CHANGELOG.md`
- Release process: `RELEASE.md`

## Automation

- CI build and sanity checks: `.github/workflows/ci.yml`
- Test matrix: `.github/workflows/test.yml`
- Secret scanning (gitleaks): `.github/workflows/gitleaks.yml`
- Dependency updates (Dependabot): `.github/dependabot.yml`
