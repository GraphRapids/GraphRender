# GraphRender

Render laid-out ELK JSON to SVG.

## Install

```bash
python -m pip install -e .
```

For SCSS/SASS themes, install Dart Sass (`sass`) and ensure it is in `PATH`.

## CLI

```bash
python main.py <layout.json> [-o output.svg] [--theme theme.css|theme.scss|theme.sass] [--no-theme]
```

Examples:

```bash
python main.py examples/largenetwork.layout.json
python main.py examples/largenetwork.layout.json --theme themes/theme.scss
python main.py examples/largenetwork.layout.json --theme src/graphrender/resources/default_theme.css -o examples/largenetwork.custom.svg
```
