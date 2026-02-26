# GraphRender - Project Context

## Purpose
GraphRender transforms laid-out ELK JSON into SVG output with theme and icon support, intended for deterministic graph visualization pipelines.

## Primary Goals
- Render correct, stable SVG from ELK layout payloads.
- Support consistent theming via CSS/SCSS/SASS inputs.
- Keep icon fetching/caching reliable and recoverable.
- Preserve readable output and predictable styling behavior.
- Support profile-driven CSS ingestion from GraphAPI bundles.

## Package Snapshot
- Python package: `graphrender`
- Entry points:
  - `python main.py`
  - `src/graphrender/__init__.py`
- Core source:
  - `src/graphrender/graphrender.py`
  - `src/graphrender/resources/default_theme.css`

## Renderer Contract
Inputs:
- ELK layout JSON with resolved geometry and edge routing.

Outputs:
- SVG text or SVG file output.
- Profile adapter kwargs for `GraphRender` (`theme_css`, metadata-preserving contract).

Behavior expectations:
- Respect existing layout coordinates (no layout pass inside renderer).
- Render nested graphs and normalize coordinates correctly.
- Embed or omit theme CSS according to flags/options.

## Theming and Icons
Theme handling:
- `.css` embedded directly.
- `.scss`/`.sass` compiled through `sass` CLI.

Icon handling:
- Fetch Iconify icons when node `icon` values are present.
- Use memory + disk cache.
- Auto-heal invalid disk cache entries.

Configuration:
- `GRAPHRENDER_ICON_CACHE_DIR` controls persistent cache location.
- Profile adapter module: `src/graphrender/profile.py`.

## Integration Notes
- Upstream layout provider: GraphLoom.
- Service integration: GraphAPI.
- Canonical theme source: GraphTheme.
- Class token normalization keeps `node.type` / `edge.type` CSS behavior stable.

## Testing Expectations
- `python -m pytest -q`
- `python -m py_compile main.py src/graphrender/__init__.py src/graphrender/graphrender.py src/graphrender/resources/__init__.py`
- `python main.py examples/input.json -o /tmp/graphrender-check.svg`

## Open Decisions / TODO
- [ ] Add golden snapshot coverage for nested graph and edge-label cases.
- [ ] Add stress tests for icon cache corruption/recovery paths.
- [ ] Formalize theme compatibility/version checks against GraphTheme metadata.

## How To Maintain This File
- Update after changes to rendering behavior, theme pipeline, or icon strategy.
- Keep file paths and contracts current.
