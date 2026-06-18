"""Fixtures for the Docker integration tests.

These run against a REAL running Home Assistant container (see docker-compose.yml)
over HTTP/websocket. Auth is bootstrapped via HA's onboarding API (no pre-seeded
auth files needed). Run with ``bash ci/test-python-integration.sh`` after the
container is up (``bash ci/e2e-up.sh`` brings everything up).

This tier must NOT have pytest-socket installed (the component tier's
pytest-homeassistant-custom-component pulls it in and blocks real network) — run
it in a separate invocation / environment.
"""

from __future__ import annotations

import time

import pytest
import requests

HA_URL = "http://localhost:8123"
HA_STARTUP_TIMEOUT = 120  # seconds


def _wait_for_ha() -> None:
    deadline = time.monotonic() + HA_STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        try:
            r = requests.get(f"{HA_URL}/api/", timeout=5)
            if r.status_code in (200, 401):
                return
        except requests.ConnectionError:
            pass
        time.sleep(2)
    raise TimeoutError(f"Home Assistant did not start within {HA_STARTUP_TIMEOUT}s")


def _complete_onboarding() -> str | None:
    """Complete onboarding if needed; return an access token (None if already done)."""
    r = requests.post(
        f"{HA_URL}/api/onboarding/users",
        json={
            "client_id": f"{HA_URL}/",
            "name": "Test",
            "username": "test",
            "password": "testtest1",
            "language": "en",
        },
        timeout=10,
    )
    if r.status_code == 200:
        code = r.json()["auth_code"]
        token = requests.post(
            f"{HA_URL}/auth/token",
            data={
                "client_id": f"{HA_URL}/",
                "code": code,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        return token.json()["access_token"]
    return None


@pytest.fixture(scope="session")
def access_token() -> str:
    _wait_for_ha()
    token = _complete_onboarding()
    if token:
        return token
    # Already onboarded — log in with the long-lived test credentials flow.
    flow = requests.post(
        f"{HA_URL}/auth/login_flow",
        json={
            "client_id": f"{HA_URL}/",
            "handler": ["homeassistant", None],
            "redirect_uri": f"{HA_URL}/",
        },
        timeout=10,
    ).json()
    step = requests.post(
        f"{HA_URL}/auth/login_flow/{flow['flow_id']}",
        json={
            "client_id": f"{HA_URL}/",
            "username": "test",
            "password": "testtest1",
        },
        timeout=10,
    ).json()
    token = requests.post(
        f"{HA_URL}/auth/token",
        data={
            "client_id": f"{HA_URL}/",
            "code": step["result"],
            "grant_type": "authorization_code",
        },
        timeout=10,
    ).json()
    return token["access_token"]


@pytest.fixture(scope="session", autouse=True)
def ensure_integration_loaded(access_token) -> None:
    """Create the config entry via the config flow if it isn't there yet.

    A template shouldn't commit runtime ``.storage`` state, so instead of seeding
    a config entry on disk we drive the (single-step) config flow over the API.
    On later runs the flow aborts with ``already_configured`` — also fine.
    """
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    resp = session.post(
        f"{HA_URL}/api/config/config_entries/flow",
        json={"handler": "example_integration"},
        timeout=10,
    )
    data = resp.json()
    if data.get("type") == "form":
        session.post(
            f"{HA_URL}/api/config/config_entries/flow/{data['flow_id']}",
            json={},
            timeout=10,
        )
    # Give HA a moment to finish setting up the entry (platforms, panel, card).
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        services = session.get(f"{HA_URL}/api/services", timeout=10).json()
        if any(b["domain"] == "example_integration" for b in services):
            return
        time.sleep(1)


@pytest.fixture
def api(access_token, ensure_integration_loaded):
    """A small REST helper bound to the authenticated session."""
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {access_token}"})

    class _Api:
        def get(self, path):
            return session.get(f"{HA_URL}{path}", timeout=10)

        def post(self, path, json=None):
            return session.post(f"{HA_URL}{path}", json=json, timeout=10)

    return _Api()
