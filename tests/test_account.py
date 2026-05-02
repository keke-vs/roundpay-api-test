import requests


def test_query_account_success(base_url, auth_headers):
    response = requests.get(f"{base_url}/api/account", headers=auth_headers, timeout=3)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "alice"
    assert body["data"]["account"] == "62220001"
    assert body["data"]["balance"] >= 0
    assert body["data"]["mobile"].startswith("13")


def test_query_account_without_token(base_url):
    response = requests.get(f"{base_url}/api/account", timeout=3)

    assert response.status_code == 401
    assert response.json()["message"] == "unauthorized"
