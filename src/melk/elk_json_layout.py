"""
Run the bundled ELK JSON layout engine (elkjson) from Python.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from enum import Enum


class ElkLayoutProvider(Enum):
    DISCO = ("disco", "DisCoLayoutProvider")
    FORCE = ("force", "ForceLayoutProvider")
    FORCE_STRESS = ("force.stress", "StressLayoutProvider")
    GRAPHVIZ_LAYOUTER = ("graphviz.layouter", "GraphvizLayoutProvider")
    LAYERED = ("layered", "LayeredLayoutProvider")
    LIBAVOID = ("libavoid", "LibavoidLayoutProvider")
    MRTREE = ("mrtree", "TreeLayoutProvider")
    RADIAL = ("radial", "RadialLayoutProvider")
    RECTPACKING = ("rectpacking", "RectPackingLayoutProvider")
    SPOREOVERLAP = ("spore", "OverlapRemovalLayoutProvider")
    SPORESHRINK = ("spore", "ShrinkTreeLayoutProvider")
    TOPDOWNPACKING = ("topdownpacking", "TopdownpackingLayoutProvider")
    VERTIFLEX = ("vertiflex", "VertiFlexLayoutProvider")

    def __init__(self, package: str, provider: str):
        self.package = package
        self.provider = provider

class ElkJsonLayout:
    """
    Execute the elkjson CLI to produce a laid-out ELK graph JSON.

    The constructor resolves the bundled elkjson binary by default, but callers
    can override it to point at another installation.
    """

    def __init__(
        self,
        elkjson_bin: str | Path | None = None,
        *,
        default_layout_provider: ElkLayoutProvider = ElkLayoutProvider.LAYERED,
        timeout: int = 30,
    ) -> None:
        root = Path(__file__).resolve().parents[2]
        default_bin = root / "elkjson" / "appassembler" / "bin" / "elkjson"
        self.elkjson_bin = Path(elkjson_bin) if elkjson_bin else default_bin
        self.default_layout_provider = default_layout_provider
        self.timeout = timeout

    def layout_file(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        *,
        pretty_json: bool = True,
        layout_provider: Optional[ElkLayoutProvider] = None,
        extra_args: Optional[List[str]] = None,
    ) -> Path:
        """
        Run elkjson on a file and write the laid-out JSON to disk.

        Returns the output path.
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"input JSON not found at {input_path}")
        if output_path is None:
            output_path = input_path.with_suffix(".layout.json")
        output_path = Path(output_path)

        if not self.elkjson_bin.exists():
            raise FileNotFoundError(f"elkjson binary not found at {self.elkjson_bin}")

        args = [
            str(self.elkjson_bin),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]

        if pretty_json:
            args.append("--pretty-json")

        provider = layout_provider or self.default_layout_provider
        args += ["--layout-provider", provider.provider]
        args += ["--layout-package", provider.package]

        if extra_args:
            args += list(extra_args)

        try:
            subprocess.run(args, check=True, capture_output=True, timeout=self.timeout)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"elkjson timed out after {self.timeout}s") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else ""
            raise RuntimeError(f"elkjson failed: {stderr.strip()}") from exc

        return output_path

    def layout_json(
        self,
        input_json: str,
        *,
        pretty_json: bool = True,
        layout_provider: Optional[ElkLayoutProvider] = None,
        extra_args: Optional[List[str]] = None,
    ) -> str:
        """
        Run layout on a JSON string and return the laid-out JSON string.

        Uses temporary files under the hood to satisfy elkjson's CLI interface.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            in_path = tmpdir_path / "graph.json"
            out_path = tmpdir_path / "graph.layout.json"
            in_path.write_text(input_json)

            self.layout_file(
                in_path,
                output_path=out_path,
                pretty_json=pretty_json,
                layout_provider=layout_provider,
                extra_args=extra_args,
            )

            return out_path.read_text()

    def layout_to_dict(
        self,
        input_path: str | Path,
        *,
        pretty_json: bool = True,
        layout_provider: Optional[ElkLayoutProvider] = None,
        extra_args: Optional[List[str]] = None,
    ) -> dict:
        """
        Run layout and return the parsed JSON without keeping an intermediate file.
        """
        layout_str = self.layout_json(
            Path(input_path).read_text(),
            pretty_json=pretty_json,
            layout_provider=layout_provider,
            extra_args=extra_args,
        )
        return json.loads(layout_str)


__all__ = ["ElkJsonLayout", "ElkLayoutProvider"]
