# Third-Party Notices

Last verified: 2026-02-16

GraphRender is licensed under Apache-2.0. This file documents third-party software, services, and content that GraphRender depends on or can consume at runtime.

## Bundled/packaged dependency

| Component | How GraphRender uses it | License | Copyright / Notice | Source |
| --- | --- | --- | --- | --- |
| `svg.py` (PyPI package: `svg.py`) | Python SVG element construction (`import svg`) | MIT | `Copyright (c) 2021 Gram` (upstream license header) | https://github.com/orsinium-labs/svg.py, https://pypi.org/project/svg.py/ |

Current project constraint and verification:
- `pyproject.toml` constraint: `svg.py>=1.0`
- Locally verified package version during this notice update: `1.10.0`

## Optional external tools (not redistributed by this repository)

| Component | How GraphRender uses it | License | Copyright / Notice | Source |
| --- | --- | --- | --- | --- |
| Dart Sass CLI (`sass`) | Optional SCSS/SASS compilation in `main.py` when `--theme` targets `.scss`/`.sass` | MIT | `Copyright (c) 2016 Google Inc.` (upstream `LICENSE`) | https://github.com/sass/dart-sass |

## Build-system tooling (not redistributed by this repository)

From `pyproject.toml` build requirements: `setuptools>=69`, `wheel`.

| Component | How GraphRender uses it | License | Source |
| --- | --- | --- | --- |
| `setuptools` | PEP 517 build backend (`setuptools.build_meta`) | MIT | https://github.com/pypa/setuptools |
| `wheel` | Build wheel artifacts | MIT | https://github.com/pypa/wheel |

## Runtime services and externally fetched content

### Iconify API service

- Endpoint used by GraphRender: `https://api.iconify.design/{icon_name}.svg`
- Usage in code: `src/graphrender/graphrender.py`
- Service site: https://iconify.design/
- Iconify software ecosystem license (for libraries/tooling): MIT (for example `@iconify/iconify`)
- Important: icon artwork licenses are collection-specific. See icon set notices below.

### Icon sets currently referenced by repository examples

The examples currently use icon prefixes `mdi`, `clarity`, and `material-symbols` (from `examples/input.json`).

| Prefix | Collection | Author | License (collection metadata) | License URL | Collection URL | Metadata version checked |
| --- | --- | --- | --- | --- | --- | --- |
| `mdi` | Material Design Icons | Pictogrammers | Apache-2.0 | https://github.com/Templarian/MaterialDesign/blob/master/LICENSE | https://icon-sets.iconify.design/mdi/ | `@iconify-json/mdi@1.2.3` |
| `clarity` | Clarity | VMware | MIT | https://github.com/vmware/clarity-assets/blob/master/LICENSE | https://icon-sets.iconify.design/clarity/ | `@iconify-json/clarity@1.2.4` |
| `material-symbols` | Material Symbols | Google | Apache-2.0 | https://github.com/google/material-design-icons/blob/master/LICENSE | https://icon-sets.iconify.design/material-symbols/ | `@iconify-json/material-symbols@1.2.55` |

Notes:
- License metadata above comes from the corresponding `@iconify-json/<prefix>` package metadata and `info.json` files.
- If you use icon prefixes not listed here, check each icon set's license before redistribution.

## ELK compatibility reference (not bundled)

- Component: Eclipse Layout Kernel (ELK)
- How GraphRender uses it: consumes ELK output JSON format
- Upstream: https://github.com/eclipse-elk/elk
- License: EPL-2.0

## Downstream obligations

- Cached icons (local cache directory or `GRAPHRENDER_ICON_CACHE_DIR`) may be subject to the original icon set licenses.
- SVG outputs generated from icon-enabled graphs may embed third-party icon vector paths (for example in `output/output.svg`), which remain subject to the originating icon licenses.
- Keep this file updated when dependencies, icon sources, or optional tooling change.

## Verification sources used for this update

- Local project files:
  - `pyproject.toml`
  - `main.py`
  - `src/graphrender/graphrender.py`
  - `examples/input.json`
- Upstream/package metadata:
  - `svg.py` PyPI metadata and repository license
  - Dart Sass repository license
  - ELK repository license
  - `@iconify/iconify` package metadata
  - `@iconify-json/mdi`, `@iconify-json/clarity`, `@iconify-json/material-symbols` metadata and `info.json`
