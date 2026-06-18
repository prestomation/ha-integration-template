"""Docker integration: a service call fires the documented bus event.

The HA config registers an automation that records the last
``example_integration_item_created`` event into an ``input_text`` helper, so we
can assert end-to-end (over real HA) that the event fired with the right payload
— exactly how an integrator would observe it.
"""

from __future__ import annotations


def test_add_item_fires_created_event(api):
    resp = api.post(
        "/api/services/example_integration/add_item?return_response",
        json={"name": "Integration shelf", "value": 5},
    )
    assert resp.status_code == 200

    # The capture automation wrote "created:<id>:<name>" into the helper.
    state = api.get("/api/states/input_text.ex_last_event").json()
    assert state["state"].startswith("created:")
    assert state["state"].endswith(":Integration shelf")
