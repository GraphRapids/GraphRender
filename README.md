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

Set `GRAPHRENDER_ICON_CACHE_DIR` to an empty string to disable disk caching entirely.

## Docker

GraphRender ships with a `Dockerfile` and `docker-compose.yml` for containerised deployment and integration testing.

The HTTP server exposes port **8080** by default.

### Build the image

```bash
docker compose build
```

### Run the service

```bash
docker compose up -d
```

### Health check

The service exposes `GET /health` which returns HTTP 200 with:

```json
{"status": "ok"}
```

Content-Type is `application/json`. This endpoint is used by the `docker-compose.yml` health check and by Graphras for readiness polling.

## Integration Testing

Integration tests run against a live instance of the service and are located in `tests/integration/`.

### Step-by-step

1. **Build the Docker image:**

   ```bash
   docker compose build
   ```

2. **Start the compose stack:**

   ```bash
   docker compose up -d
   ```

3. **Wait for the service to be healthy:**

   ```bash
   docker compose ps
   ```

   The `graph-render` service should show status `healthy`.

4. **Run the integration tests:**

   ```bash
   pytest tests/integration/
   ```

   By default, tests target `http://localhost:8080`. Override with the `SERVICE_URL` environment variable:

   ```bash
   SERVICE_URL=http://localhost:9090 pytest tests/integration/
   ```

5. **Tear down:**

   ```bash
   docker compose down
   ```

### Notes

- Integration tests are **not** run by the default `pytest` invocation (unit tests only). They require a live service.
- Tests are self-contained and idempotent — they create their own test data and clean up after themselves.
- The `SERVICE_URL` environment variable controls which instance the tests target.

## Testing

Run unit tests:

```bash
pytest tests/ --ignore=tests/integration
```

Run integration tests (requires a running service — see [Integration Testing](#integration-testing)):

```bash
pytest tests/integration/
```

## Automation

CI/CD is managed via GitHub Actions workflows:

- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — main CI pipeline
- [`.github/workflows/test.yml`](.github/workflows/test.yml) — test suite
- [`.github/workflows/gitleaks.yml`](.github/workflows/gitleaks.yml) — secret scanning with Gitleaks
- [`.github/workflows/release.yml`](.github/workflows/release.yml) — release automation

See [`.github/dependabot.yml`](.github/dependabot.yml) for dependency update configuration.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for contribution guidelines.

## Security

See [`SECURITY.md`](./SECURITY.md) for the security policy and vulnerability reporting instructions.

## Governance

This project follows the [Code of Conduct](./CODE_OF_CONDUCT.md).

For release process details, see [`RELEASE.md`](./RELEASE.md).

## Third-Party Notices

See [`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md) for third-party license attributions.

## License

This project is licensed under the [Apache License 2.0](./LICENSE).
