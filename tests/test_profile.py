import pytest
import requests


def test_update_profile_success(base_url, auth_headers):
    response = requests.patch(
        f"{base_url}/api/profile",
        json={"nickname": "Alice Test", "mobile": "13900000001"},
        headers=auth_headers,
        timeout=3,
    )

    assert response.status_code == 200
    assert response.json()["data"]["nickname"] == "Alice Test"
    assert response.json()["data"]["mobile"] == "13900000001"


@pytest.mark.parametrize("mobile", ["123456", "23800000001", "1380000000a"])
def test_update_profile_mobile_format(base_url, auth_headers, mobile):
    response = requests.patch(
        f"{base_url}/api/profile",
        json={"nickname": "Alice", "mobile": mobile},
        headers=auth_headers,
        timeout=3,
    )

    assert response.status_code == 400
    assert response.json()["message"] == "mobile format is invalid"

