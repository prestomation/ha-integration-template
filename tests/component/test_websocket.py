"""Component tests: the panel/card websocket commands delegate to the store."""

from __future__ import annotations

from custom_components.example_integration.const import DOMAIN


async def test_websocket_add_list_update_delete(hass, setup_entry, hass_ws_client):
    client = await hass_ws_client(hass)

    # list -> empty
    await client.send_json({"id": 1, "type": f"{DOMAIN}/list"})
    res = await client.receive_json()
    assert res["success"] and res["result"]["items"] == []

    # add
    await client.send_json({"id": 2, "type": f"{DOMAIN}/add", "name": "Shelf", "value": 2})
    res = await client.receive_json()
    assert res["success"]
    item_id = res["result"]["item"]["id"]

    # list -> one item
    await client.send_json({"id": 3, "type": f"{DOMAIN}/list"})
    res = await client.receive_json()
    assert [i["id"] for i in res["result"]["items"]] == [item_id]

    # update
    await client.send_json(
        {"id": 4, "type": f"{DOMAIN}/update", "item_id": item_id, "value": 7}
    )
    res = await client.receive_json()
    assert res["success"] and res["result"]["item"]["value"] == 7

    # delete
    await client.send_json({"id": 5, "type": f"{DOMAIN}/delete", "item_id": item_id})
    res = await client.receive_json()
    assert res["success"]

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    res = await client.receive_json()
    assert res["result"]["items"] == []


async def test_websocket_add_rejects_invalid(hass, setup_entry, hass_ws_client):
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": f"{DOMAIN}/add", "name": "   "})
    res = await client.receive_json()
    assert not res["success"]
    assert res["error"]["code"] == "invalid_format"


async def test_websocket_delete_unknown(hass, setup_entry, hass_ws_client):
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": f"{DOMAIN}/delete", "item_id": "nope"})
    res = await client.receive_json()
    assert not res["success"]
    assert res["error"]["code"] == "not_found"
