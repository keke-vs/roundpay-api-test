import requests


def test_query_funds_success(base_url):
    response = requests.get(f"{base_url}/api/funds?page=1&pageSize=10", timeout=3)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] >= 1
    assert "fundId" in body["data"]["items"][0]


def test_buy_fund_success(base_url, auth_headers):
    response = requests.post(
        f"{base_url}/api/fund/buy",
        json={"fundId": "FUND001", "amount": 100.00},
        headers=auth_headers,
        timeout=3,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "SUCCESS"
    assert body["data"]["fundId"] == "FUND001"


def test_buy_fund_less_than_min_amount(base_url, auth_headers):
    response = requests.post(
        f"{base_url}/api/fund/buy",
        json={"fundId": "FUND001", "amount": 1.00},
        headers=auth_headers,
        timeout=3,
    )

    assert response.status_code == 400
    assert response.json()["message"] == "amount is less than minimum purchase amount"


def test_buy_closed_fund_failed(base_url, auth_headers):
    response = requests.post(
        f"{base_url}/api/fund/buy",
        json={"fundId": "FUND002", "amount": 100.00},
        headers=auth_headers,
        timeout=3,
    )

    assert response.status_code == 400
    assert response.json()["message"] == "fund is not available"

