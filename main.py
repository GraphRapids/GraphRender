import argparse
import subprocess
import sys
from pathlib import Path

# Make the local package importable without installation.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from graphrender import ElkGraphSvg


def load_theme_css(theme_path: Path) -> str:
    """Load CSS directly or compile SCSS/SASS to CSS via the `sass` CLI."""
    suffix = theme_path.suffix.lower()
    if suffix == ".css":
        return theme_path.read_text(encoding="utf-8")
    if suffix not in {".scss", ".sass"}:
        raise ValueError(
            f"Unsupported theme extension '{theme_path.suffix}'. Use .css, .scss, or .sass."
        )
    try:
        proc = subprocess.run(
            ["sass", "--no-source-map", str(theme_path)],
            cwd=str(theme_path.parent),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "SCSS/SASS theme compilation requires the `sass` CLI in PATH."
        ) from exc
    if proc.returncode != 0:
        raise RuntimeError(f"sass compilation failed:\n{proc.stderr.strip()}")
    return proc.stdout


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Render a laid-out ELK JSON file to SVG."
    )
    parser.add_argument(
        "input",
        help="Path to laid-out ELK JSON input.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output SVG (default: <input_stem>.svg).",
    )
    parser.add_argument(
        "--theme",
        help="Theme file path (.css, .scss, or .sass). Defaults to bundled theme.",
    )
    parser.add_argument(
        "--no-theme",
        action="store_true",
        help="Disable embedding theme CSS into the SVG.",
    )
    args = parser.parse_args(argv)

    input_arg = Path(args.input)
    input_path = input_arg if input_arg.is_absolute() else (ROOT / input_arg)
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_path}")
    output_path = (
        Path(args.output)
        if args.output
        else input_path.with_name(f"{input_path.stem}.svg")
    )
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    theme_css = None
    if args.theme:
        theme_arg = Path(args.theme)
        theme_path = theme_arg if theme_arg.is_absolute() else (ROOT / theme_arg)
        if not theme_path.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_path}")
        theme_css = load_theme_css(theme_path)

    graph = ElkGraphSvg.from_file(
        input_path,
        embed_theme=not args.no_theme,
        theme_css=theme_css,
    )
    graph.write(output_path)
    print(f"Rendered: {output_path}")

if __name__ == "__main__":
    main(sys.argv[1:])
