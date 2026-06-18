"""Pytest configuration for the pure unit tests.

The model and event-payload builders are pure Python (they import nothing from
Home Assistant), so we load them in isolation here under a synthetic ``ex``
package. This lets the high-value core tests run without the full HA test
harness (``pip install pytest`` is enough) while still pointing coverage at the
real source files in ``custom_components/example_integration``.

Tests that need a real Home Assistant runtime live under ``tests/component``
(in-process HA via pytest-homeassistant-custom-component) and
``tests/integration`` (Docker HA).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

_COMPONENT_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "example_integration"
)


def _load_pure_modules() -> None:
    """Load const/models/events as an isolated ``ex`` package (no HA imports)."""
    if "ex" in sys.modules:
        return
    pkg = types.ModuleType("ex")
    pkg.__path__ = [str(_COMPONENT_DIR)]  # type: ignore[attr-defined]
    sys.modules["ex"] = pkg
    for name in ("const", "models", "events"):
        spec = importlib.util.spec_from_file_location(
            f"ex.{name}", str(_COMPONENT_DIR / f"{name}.py")
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"ex.{name}"] = module
        spec.loader.exec_module(module)


_load_pure_modules()
