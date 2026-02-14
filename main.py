import json
import sys
from pathlib import Path

# Make the local package importable without installation.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from elkpydantic.builder import MinimalGraphIn, build_canvas,  _load_settings, ElkSettings, sample_settings
from melk import ElkGraphSvg, ElkJsonLayout, ElkLayoutProvider

def enrich_with_elkpydantic(input_path: Path, settings: ElkSettings) -> str:
    """Convert a minimal graph JSON into ELK-compatible JSON."""
    payload = input_path.read_text()
    minimal_graph = MinimalGraphIn.model_validate_json(payload)
    canvas = build_canvas(minimal_graph, settings)
    enriched = canvas.model_dump(by_alias=True, exclude_none=True)
    return json.dumps(enriched, indent=2)


def main() -> None:
    # Allow overriding the input file; default to the bundled example.
    input_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("examples/udland.json")
    input_path = input_arg if input_arg.is_absolute() else (ROOT / input_arg)

    settings = _load_settings("examples/elk_settings.example.toml")
    #settings = sample_settings()

    enriched_json = enrich_with_elkpydantic(input_path,settings)
    enriched_path = input_path.with_name(f"{input_path.stem}.elk.json")
    enriched_path.write_text(enriched_json)

    layout = ElkJsonLayout()
    laid_out_json = layout.layout_json(enriched_json, layout_provider=ElkLayoutProvider.LAYERED)
    layout_path = input_path.with_name(f"{input_path.stem}.layout.json")
    layout_path.write_text(laid_out_json)

    elk_svg = ElkGraphSvg.from_json(laid_out_json)
    svg_str = elk_svg.to_string()
    svg_path = input_path.with_name(f"{input_path.stem}.svg")
    svg_path.write_text(svg_str)

    print(f"Enriched: {enriched_path}")
    print(f"Laid out: {layout_path}")
    print(f"Rendered: {svg_path}")

if __name__ == "__main__":
    main()
