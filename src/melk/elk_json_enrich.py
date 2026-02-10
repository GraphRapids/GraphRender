from __future__ import annotations

import copy
import json
from typing import Any, Dict, List, MutableMapping

from .elk_model import ElkModel

__all__ = ["ElkJsonEnrich"]


class ElkJsonEnrich:
    """
    Fill missing ELK graph values using the bundled defaults (elk_defaults_json).
    Existing values are preserved; defaults only fill gaps. Defaults are sourced
    from the Pydantic model definitions in elk_model.py, so adding new defaults
    to that model automatically flows here.
    """

    # Public API ---------------------------------------------------------
    def apply_to_dict(self, graph: Dict) -> Dict:
        """Return a copy of `graph` with defaults applied."""
        # Validate+hydrate using the ElkModel defaults
        model = ElkModel.model_validate(graph)
        return model.model_dump(by_alias=True, exclude_none=True)

    def apply_to_json(self, json_str: str) -> str:
        """Return a JSON string with defaults applied."""
        data = json.loads(json_str)
        updated = self.apply_to_dict(data)
        return json.dumps(updated)
