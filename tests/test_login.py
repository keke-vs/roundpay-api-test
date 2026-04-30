import pytest
import requests
from jsonschema import validate

from tests.schemas import LOGIN_SCHEMA, SUCCESS_SCHEMA


def test_login_success(base_url):
    response = requests.post(
        f"{base_url}/api/login",
        json={"username": "alice", "password": "123456"},
        timeout=3,
    )

    assert response.status_code == 200
    body = response.json()
    validate(body, LOGIN_SCHEMA)
    assert body["data"]["token"]


@pytest.mark.parametrize(
    "payload, expected_message",
    [
        ({"username": "alice", "password": "wrong"}, "username or password is wrong"),
        ({"username": "", "password": "123456"}, "username and password are required"),
        ({"username": "alice", "password": ""}, "username and password are required"),
    ],
)
def test_login_failed(base_url, payload, expected_message):
    response = requests.post(f"{base_url}/api/login", json=payload, timeout=3)

    assert response.status_code in [400, 401]
    body = response.json()
    validate(body, SUCCESS_SCHEMA)
    assert body["message"] == expected_message

