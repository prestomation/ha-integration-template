"""The pure core imports nothing from Home Assistant.

``tests/unit/conftest.py`` loads the modules in ``_PURE_MODULES`` with no Home
Assistant installed, and the mutation gate scores them. A ``homeassistant`` import
in one of them would break the fast unit tier, and the design doc's module map
would then state a rule that the code does not keep. So the list in the conftest
is the one source, and this file checks the code and the doc against it.
"""

from __future__ import annotations

import ast
import json
import re
import tomllib
from pathlib import Path

import conftest
import pytest

_ROOT = Path(__file__).resolve().parents[2]
_COMPONENT = _ROOT / "custom_components" / "example_integration"


def _bad_imports(source: str, pure: set[str]) -> list[str]:
    """Each import in *source* that leaves the pure core."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if a.name.startswith("homeassistant")]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if not node.level:
                if module.startswith("homeassistant"):
                    found.append(module)
            elif module:  # `from .const import X`
                if module.split(".")[0] not in pure:
                    found.append(f".{module}")
            else:  # `from . import const`
                found += [f".{a.name}" for a in node.names if a.name not in pure]
    return found


@pytest.mark.parametrize("name", conftest._PURE_MODULES)
def test_a_pure_module_imports_only_the_pure_core(name: str) -> None:
    source = (_COMPONENT / f"{name}.py").read_text(encoding="utf-8")
    assert _bad_imports(source, set(conftest._PURE_MODULES)) == []


def test_the_check_sees_each_kind_of_import() -> None:
    source = (
        "import homeassistant.core\n"
        "from homeassistant.util import dt\n"
        "from .store import ExampleStore\n"
        "from . import coordinator, const\n"
        "from .const import DOMAIN\n"
        "import json\n"
    )
    assert _bad_imports(source, {"const"}) == [
        "homeassistant.core",
        "homeassistant.util",
        ".store",
        ".coordinator",
    ]


def test_the_design_doc_names_the_same_pure_core() -> None:
    doc = (_ROOT / "docs" / "design" / "architecture.md").read_text(encoding="utf-8")
    row = next(line for line in doc.splitlines() if line.startswith("| Pure core |"))
    named = re.findall(r"`(\w+)\.py`", row.split("|")[2])
    assert sorted(named) == sorted(conftest._PURE_MODULES)


def test_the_mutation_gate_is_the_same_for_both_languages() -> None:
    """``[tool.mutation-gate] break`` and Stryker's ``thresholds.break`` agree.

    ``ci/mutation_report.py`` checks this too, but only in the mutation job, which
    skips a PR that changes no mutable code. This runs on every PR.
    """
    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    stryker = json.loads((_ROOT / "stryker.conf.json").read_text(encoding="utf-8"))
    python_gate = pyproject["tool"]["mutation-gate"]["break"]
    assert stryker["thresholds"]["break"] == python_gate
