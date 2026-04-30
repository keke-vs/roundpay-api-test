import uuid

import pytest
import requests
from jsonschema import validate

from tests.schemas import TRANSFER_SCHEMA


def test_transfer_success(base_url, auth_headers):
    payload = {
        "toAccount": "62220002",
        "amount": 88.66,
        "requestId": f"REQ-{uuid.uuid4()}",
    }

    response = requests.post(
        f"{base_url}/api/transfer",
        json=payload,
        headers=auth_headers,
        timeout=3,
    )

    assert response.status_code == 200
    body = response.json()
    validate(body, TRANSFER_SCHEMA)
    assert body["data"]["amount"] == 88.66
    assert body["data"]["fromBalance"] >= 0


@pytest.mark.parametrize("amount", [0, -1, 1.234])
def test_transfer_amount_boundary(base_url, auth_headers, amount):
    response = requests.post(
        f"{base_url}/api/transfer",
        json={
            "toAccount": "62220002",
            "amount": amount,
            "requestId": f"REQ-{uuid.uuid4()}",
        },
        headers=auth_headers,
        timeout=3,
    )

    assert response.status_code == 400
    assert response.json()["code"] == 400


def test_transfer_idempotent_by_request_id(base_url, auth_headers):
    request_id = f"REQ-{uuid.uuid4()}"
    payload = {"toAccount": "62220002", "amount": 20.00, "requestId": request_id}

    first = requests.post(
        f"{base_url}/api/transfer",
        json=payload,
        headers=auth_headers,
        timeout=3,
    ).json()
    second = requests.post(
        f"{base_url}/api/transfer",
        json=payload,
        headers=auth_headers,
        timeout=3,
    ).json()

    assert first["data"] == second["data"]


def test_transfer_without_token(base_url):
    response = requests.post(
        f"{base_url}/api/transfer",
        json={"toAccount": "62220002", "amount": 10, "requestId": "REQ-NO-TOKEN"},
        timeout=3,
    )

    assert response.status_code == 401
    assert response.json()["message"] == "unauthorized"

