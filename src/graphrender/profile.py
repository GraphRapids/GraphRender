from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ResolvedProfileRenderBundle:
    profile_id: str
    profile_version: int
    checksum: str
    render_css: str


def css_class_token(value: Any) -> str:
    token = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "").strip().lower())
    token = token.strip("-_")
    if not token:
        return "type-unknown"
    if token[0].isdigit():
        return f"type-{token}"
    return token


def _require(bundle: Mapping[str, Any], field: str) -> Any:
    if field not in bundle:
        raise ValueError(f"Profile bundle is missing required field '{field}'.")
    return bundle[field]


def resolve_profile_render_bundle(bundle: Mapping[str, Any]) -> ResolvedProfileRenderBundle:
    profile_id = str(_require(bundle, "profileId"))
    profile_version = int(_require(bundle, "profileVersion"))
    checksum = str(_require(bundle, "checksum"))
    render_css = str(_require(bundle, "renderCss"))

    if not render_css.strip():
        raise ValueError("Profile bundle field 'renderCss' must not be empty.")

    return ResolvedProfileRenderBundle(
        profile_id=profile_id,
        profile_version=profile_version,
        checksum=checksum,
        render_css=render_css,
    )


def render_kwargs_from_profile_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    resolved = resolve_profile_render_bundle(bundle)
    return {
        "theme_css": resolved.render_css,
        "embed_theme": True,
        "theme_id": "default",
    }
