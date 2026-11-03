"""Tests that the integration does not block the event loop.

The autouse ``blockbuster`` fixture in ``conftest.py`` does the checking. Code
that has a frame of the integration on the stack and makes a blocking call in a
running event loop fails with ``BlockingError``. The message has the file and
line of the call.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from blockbuster import BlockingError

import custom_components.example_integration as component
from custom_components.example_integration.const import DOMAIN

# The guard source blocks on purpose.
_BLOCKING_SOURCE = "import time\n\nasync def blocking():\n    time.sleep(0.01)\n"


def _run_guard_code(file_name: str) -> None:
    """Run ``_BLOCKING_SOURCE`` as if it were a file named ``file_name``."""
    namespace: dict = {}
    exec(compile(_BLOCKING_SOURCE, file_name, "exec"), namespace)
    asyncio.run(namespace["blocking"]())


def test_blockbuster_finds_a_blocking_call_in_our_code():
    """Guard test: a fixture that does nothing would pass every other test."""
    guard_file = str(Path(component.__file__).parent / "_blocking_guard.py")
    with pytest.raises(BlockingError):
        _run_guard_code(guard_file)


def test_blockbuster_ignores_a_blocking_call_outside_our_code():
    """Calls from Home Assistant core or the harness are not ours to fix."""
    _run_guard_code("/somewhere/else/other_module.py")


async def test_setup_and_service_calls_do_not_block(hass, setup_entry):
    """Set up the entry and call each service. A blocking call fails the test."""
    await hass.services.async_call(
        DOMAIN, "add_item", {"name": "Shelf", "value": 1}, blocking=True
    )
    await hass.async_block_till_done()
