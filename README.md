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

Set `GRAPHRENDER_ICON_CACHE_DIR` to an empty string to disable persistent disk caching.

## Integration Testing

GraphRender includes a lightweight HTTP server and Docker setup for integration testing.

### HTTP Server

The server exposes two endpoints:

| Endpoint  | Method | Description                            |
|-----------|--------|----------------------------------------|
| `/health` | `GET`  | Returns `{"status": "ok"}` with HTTP 200 |
| `/render` | `POST` | Accepts ELK JSON body, returns SVG     |

**Port:** `8080` (configurable via the `GRAPHRENDER_PORT` environment variable).

### Building the Docker Image

```bash
docker build -t graph-render .
```

### Starting with Docker Compose

```bash
docker compose up -d
```

Wait for the service to become healthy:

```bash
docker compose ps
# graph-render should show status "healthy"
```

Or check manually:

```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

### Running Integration Tests

Integration tests live in `tests/integration/` and require a running service instance:

```bash
# 1. Start the service
docker compose up -d

# 2. Run integration tests
SERVICE_URL=http://localhost:8080 pytest tests/integration/ -v

# 3. Tear down
docker compose down
```

Integration tests are automatically **skipped** when `SERVICE_URL` is not set, so the default `pytest` invocation only runs unit tests.

### Teardown

```bash
docker compose down
```

## Theming Notes

GraphRender supports three theme formats:

- **CSS** — embedded directly into the SVG `<style>` block
- **SCSS / SASS** — compiled via the Dart Sass CLI (`sass`) before embedding

The default theme is bundled at `src/graphrender/resources/default_theme.css` and is embedded automatically unless `--no-theme` is passed.

Custom themes override the default:

```bash
python main.py examples/input.json --theme themes/theme.scss -o output/themed.svg
```

Theme variables are defined in `themes/_variables.scss` and imported by `themes/theme.scss`.

## Troubleshooting

| Problem | Solution |
|---|---|
| `sass` not found | Install Dart Sass: `npm install -g sass` or download from the [Sass releases](https://github.com/sass/dart-sass/releases) |
| Icon not rendering | Check network connectivity; icon SVGs are fetched from the Iconify API on first use |
| Corrupted icon cache | Delete the cache directory or set `GRAPHRENDER_ICON_CACHE_DIR` to a fresh path |
| SVG output is empty | Verify the input JSON contains `width`/`height` on the root and geometry on child nodes |

## Development

```bash
# Clone and set up
git clone https://github.com/Faerkeren/GraphRender.git
cd GraphRender
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run unit tests
pytest

# Run a quick render
python main.py examples/input.json -o output/dev-test.svg
```

## Project Layout

```
src/graphrender/            Core rendering library
src/graphrender/resources/  Default theme and static assets
src/graphrender/server.py   Lightweight HTTP server (health + render)
tests/                      Unit tests
tests/integration/          Integration tests (require running service)
themes/                     SCSS theme sources
examples/                   Example ELK JSON input files
output/                     Default output directory
docs/adr/                   Architecture Decision Records
```

## Governance

See [CONTRIBUTING.md](./CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## Automation

CI/CD is managed via GitHub Actions:

- **CI** — linting and build checks on every push
- **Tests** — unit test suite on every push and pull request
- **Secret Scan** — Gitleaks scanning for leaked credentials
- **Release** — automated release workflow

## Acknowledgements

GraphRender is part of the [GraphRapids](https://github.com/Faerkeren) suite.

## Third-Party Notices

See [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](./LICENSE) for the full text.
