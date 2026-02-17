from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import main as cli_main


class DummyRenderer:
    def __init__(self) -> None:
        self.writes: list[Path] = []

    def write(self, path: Path) -> None:
        self.writes.append(Path(path))


class StubGraphRender:
    calls: list[tuple[tuple, dict]] = []
    renderer = DummyRenderer()

    @classmethod
    def reset(cls) -> None:
        cls.calls = []
        cls.renderer = DummyRenderer()

    @classmethod
    def from_file(cls, *args, **kwargs):
        cls.calls.append((args, kwargs))
        return cls.renderer


def write_input(path: Path) -> None:
    path.write_text(json.dumps({"id": "root", "children": [], "edges": []}), encoding="utf-8")


def test_load_theme_css_reads_css_file(tmp_path):
    css_path = tmp_path / "theme.css"
    css_path.write_text("svg { color: red; }", encoding="utf-8")

    result = cli_main.load_theme_css(css_path)

    assert result == "svg { color: red; }"


def test_load_theme_css_rejects_unsupported_extension(tmp_path):
    txt_path = tmp_path / "theme.txt"
    txt_path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported theme extension"):
        cli_main.load_theme_css(txt_path)


def test_load_theme_css_raises_if_sass_binary_missing(monkeypatch, tmp_path):
    scss_path = tmp_path / "theme.scss"
    scss_path.write_text("$c: red;", encoding="utf-8")

    def raising(*args, **kwargs):
        raise FileNotFoundError("sass missing")

    monkeypatch.setattr(cli_main.subprocess, "run", raising)

    with pytest.raises(RuntimeError, match="requires the `sass` CLI"):
        cli_main.load_theme_css(scss_path)


def test_load_theme_css_raises_on_sass_failure(monkeypatch, tmp_path):
    scss_path = tmp_path / "theme.scss"
    scss_path.write_text("$c: red;", encoding="utf-8")

    monkeypatch.setattr(
        cli_main.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=["sass"], returncode=2, stdout="", stderr="compile failed"),
    )

    with pytest.raises(RuntimeError, match="sass compilation failed"):
        cli_main.load_theme_css(scss_path)


def test_load_theme_css_returns_compiled_sass_output(monkeypatch, tmp_path):
    scss_path = tmp_path / "theme.scss"
    scss_path.write_text("$c: red;", encoding="utf-8")

    monkeypatch.setattr(
        cli_main.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=["sass"], returncode=0, stdout="svg{color:red;}\n", stderr=""),
    )

    result = cli_main.load_theme_css(scss_path)

    assert result == "svg{color:red;}\n"


def test_main_raises_when_input_is_missing(tmp_path):
    missing = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Input JSON not found"):
        cli_main.main([str(missing)])


def test_main_raises_when_theme_file_missing(monkeypatch, tmp_path):
    input_path = tmp_path / "graph.json"
    write_input(input_path)
    monkeypatch.setattr(cli_main, "GraphRender", StubGraphRender)
    StubGraphRender.reset()

    with pytest.raises(FileNotFoundError, match="Theme file not found"):
        cli_main.main([str(input_path), "--theme", str(tmp_path / "missing.css")])


def test_main_uses_default_output_and_theme_settings(monkeypatch, tmp_path, capsys):
    input_path = tmp_path / "graph.json"
    write_input(input_path)

    monkeypatch.setattr(cli_main, "GraphRender", StubGraphRender)
    StubGraphRender.reset()

    cli_main.main([str(input_path)])

    args, kwargs = StubGraphRender.calls[0]
    assert Path(args[0]) == input_path
    assert kwargs == {"embed_theme": True, "theme_css": None}
    assert StubGraphRender.renderer.writes == [tmp_path / "graph.svg"]
    assert f"Rendered: {tmp_path / 'graph.svg'}" in capsys.readouterr().out


def test_main_respects_no_theme_flag(monkeypatch, tmp_path):
    input_path = tmp_path / "graph.json"
    write_input(input_path)

    monkeypatch.setattr(cli_main, "GraphRender", StubGraphRender)
    StubGraphRender.reset()

    cli_main.main([str(input_path), "--no-theme"])

    _, kwargs = StubGraphRender.calls[0]
    assert kwargs["embed_theme"] is False
    assert kwargs["theme_css"] is None


def test_main_loads_theme_css_and_passes_to_renderer(monkeypatch, tmp_path):
    input_path = tmp_path / "graph.json"
    theme_path = tmp_path / "theme.css"
    write_input(input_path)
    theme_path.write_text("svg{stroke:red;}", encoding="utf-8")

    monkeypatch.setattr(cli_main, "GraphRender", StubGraphRender)
    StubGraphRender.reset()

    cli_main.main([str(input_path), "--theme", str(theme_path)])

    _, kwargs = StubGraphRender.calls[0]
    assert kwargs["embed_theme"] is True
    assert kwargs["theme_css"] == "svg{stroke:red;}"


def test_main_resolves_relative_paths_against_root(monkeypatch, tmp_path):
    input_path = tmp_path / "input.json"
    theme_path = tmp_path / "theme.css"
    write_input(input_path)
    theme_path.write_text("svg{fill:blue;}", encoding="utf-8")

    monkeypatch.setattr(cli_main, "ROOT", tmp_path)
    monkeypatch.setattr(cli_main, "GraphRender", StubGraphRender)
    StubGraphRender.reset()

    cli_main.main(["input.json", "--theme", "theme.css", "-o", "out/rendered.svg"])

    args, kwargs = StubGraphRender.calls[0]
    assert Path(args[0]) == input_path
    assert kwargs["theme_css"] == "svg{fill:blue;}"
    assert StubGraphRender.renderer.writes == [tmp_path / "out" / "rendered.svg"]
