import json
import sys
from pathlib import Path

# Make the local package importable without installation.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from melk import ElkGraphSvg, ElkJsonLayout, ElkJsonEnrich

def main():
    # Read input JSON (user-facing I/O kept outside the library)
    input_json = Path("examples/sample3.json").read_text()

    # Apply defaults, run layout, and render—entirely in-memory
    enricher = ElkJsonEnrich()
    enriched_json = enricher.apply_to_json(input_json)

    #print indented for readability, not compact
    enriched_json = json.dumps(json.loads(enriched_json), indent=2)

    Path("examples/sample3.enriched.json").write_text(enriched_json)
    
    layout = ElkJsonLayout()
    laid_out_json = layout.layout_json(enriched_json)
    Path("examples/sample3.layout.json").write_text(laid_out_json)
    elk_svg = ElkGraphSvg.from_json(laid_out_json)
    svg_str = elk_svg.to_string()

    # Write outputs (user-facing I/O)
    
    Path("examples/sample3.svg").write_text(svg_str)

if __name__ == "__main__":
    main()
