import pytest
from pydantic import SecretStr

from app.core.config import settings

MESSAGE = {
    "routingHeader": {
        "operationType": "retrieve",
        "messageId": "message-1",
        "sourceId": "nsi",
        "destinationId": "dev_api",
    },
    "datagram": {"x-datagram": {"Human": {}}},
}


async def test_nsi_disabled_without_credentials(client, monkeypatch):
    monkeypatch.setattr(settings, "nsi_basic_username", "")
    monkeypatch.setattr(settings, "nsi_basic_password", SecretStr(""))
    response = await client.post("/nsirest/", json=MESSAGE)
    assert response.status_code == 503


async def test_nsi_auth_required(client, monkeypatch):
    monkeypatch.setattr(settings, "nsi_basic_username", "user")
    monkeypatch.setattr(settings, "nsi_basic_password", SecretStr("password"))
    for auth in (None, ("user", "wrong")):
        response = await client.post("/nsirest/", json=MESSAGE, auth=auth)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Basic"


@pytest.mark.parametrize("operation", ["retrieve", "insert", "update", "delete", "commit"])
async def test_nsi_never_claims_unimplemented_operation_succeeded(client, monkeypatch, operation):
    monkeypatch.setattr(settings, "nsi_basic_username", "user")
    monkeypatch.setattr(settings, "nsi_basic_password", SecretStr("password"))
    monkeypatch.setattr(settings, "nsi_destination_id", "dev_api")
    payload = {**MESSAGE, "routingHeader": {**MESSAGE["routingHeader"], "operationType": operation}}
    response = await client.post("/nsirest/", json=payload, auth=("user", "password"))
    body = response.json()
    assert body["callCC"] == 2
    assert body["routingHeader"] == {
        "sourceId": "dev_api",
        "destinationId": "nsi",
        "correlationId": "message-1",
    }


async def test_nsi_rejects_wrong_destination(client, monkeypatch):
    monkeypatch.setattr(settings, "nsi_basic_username", "user")
    monkeypatch.setattr(settings, "nsi_basic_password", SecretStr("password"))
    monkeypatch.setattr(settings, "nsi_destination_id", "dev_api")
    payload = {**MESSAGE, "routingHeader": {**MESSAGE["routingHeader"], "destinationId": "wrong"}}
    assert (await client.post("/nsirest/", json=payload, auth=("user", "password"))).status_code == 400
