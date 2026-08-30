"""Pytest configuration for the pure unit tests.

The model, the event-payload builders and the API-surface index are pure Python
(they import nothing from
Home Assistant), so we load them in isolation here under a synthetic ``ex``
package. This lets the high-value core tests run without the full HA test
harness (``pip install pytest`` is enough) while still pointing coverage at the
real source files in ``custom_components/example_integration``.

The modules are *executed* under their real dotted name
(``custom_components.example_integration.<mod>``) with stub parent packages, so
the package ``__init__.py`` — which does import Home Assistant — never runs.
``ex.<mod>`` is then registered as an alias of the same module object, which is
what the tests import. Executing under the real name matters for mutation
testing: mutmut derives a mutant's key from the file path and matches it against
the function's ``__module__``, so a module executed as ``ex.models`` would leave
every mutant looking untested.

**This lives in ``tests/unit/``, not ``tests/``, on purpose.** The stub parent
packages it installs would otherwise shadow the real integration for the
component tier, where Home Assistant imports
``custom_components.example_integration`` itself and needs the actual
``async_setup_entry``. Tests that need a real Home Assistant runtime live under
``tests/component`` (in-process HA via pytest-homeassistant-custom-component)
and ``tests/integration`` (Docker HA).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_CUSTOM_COMPONENTS_DIR = _ROOT / "custom_components"
_COMPONENT_DIR = _CUSTOM_COMPONENTS_DIR / "example_integration"

_PKG = "custom_components.example_integration"
_PURE_MODULES = ("const", "models", "events", "api_surface")


def _stub_package(name: str, path: Path) -> None:
    """Register an empty package for ``name`` so relative imports resolve.

    Real ``custom_components.example_integration`` would execute an
    ``__init__.py`` full of Home Assistant imports; the stub gives the pure
    modules a parent to hang ``from .const import ...`` off without it.
    """
    if name in sys.modules:
        return
    pkg = types.ModuleType(name)
    pkg.__path__ = [str(path)]  # type: ignore[attr-defined]
    sys.modules[name] = pkg


def _load_pure_modules() -> None:
    """Load the pure modules without importing Home Assistant.

    Order matters: ``const`` is loaded first because ``api_surface`` does
    ``from . import const``.
    """
    if "ex" in sys.modules:
        return
    _stub_package("custom_components", _CUSTOM_COMPONENTS_DIR)
    _stub_package(_PKG, _COMPONENT_DIR)
    for name in _PURE_MODULES:
        spec = importlib.util.spec_from_file_location(
            f"{_PKG}.{name}", str(_COMPONENT_DIR / f"{name}.py")
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"{_PKG}.{name}"] = module
        spec.loader.exec_module(module)
    # ``ex`` is the short alias the tests import; it points at the very same
    # module objects, so there is only ever one copy of the pure core loaded.
    sys.modules["ex"] = sys.modules[_PKG]
    for name in _PURE_MODULES:
        sys.modules[f"ex.{name}"] = sys.modules[f"{_PKG}.{name}"]


_load_pure_modules()
