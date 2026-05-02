import uuid

import requests


def test_query_transactions_success(base_url, auth_headers):
    response = requests.get(
        f"{base_url}/api/transactions",
        headers=auth_headers,
        timeout=3,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert isinstance(body["data"]["items"], list)


def test_transfer_generates_transaction_record(base_url, auth_headers):
    response = requests.post(
        f"{base_url}/api/transfer",
        json={
            "toAccount": "62220002",
            "amount": 12.34,
            "requestId": f"REQ-{uuid.uuid4()}",
        },
        headers=auth_headers,
        timeout=3,
    )
    assert response.status_code == 200

    transactions = requests.get(
        f"{base_url}/api/transactions",
        headers=auth_headers,
        timeout=3,
    ).json()["data"]["items"]

    assert transactions[0]["type"] == "TRANSFER_OUT"
    assert transactions[0]["amount"] == -12.34
    assert "62220002" in transactions[0]["description"]


def test_fund_buy_generates_transaction_record(base_url, auth_headers):
    response = requests.post(
        f"{base_url}/api/fund/buy",
        json={"fundId": "FUND001", "amount": 50.00},
        headers=auth_headers,
        timeout=3,
    )
    assert response.status_code == 200

    transactions = requests.get(
        f"{base_url}/api/transactions",
        headers=auth_headers,
        timeout=3,
    ).json()["data"]["items"]

    assert transactions[0]["type"] == "FUND_BUY"
    assert transactions[0]["amount"] == -50.00
    assert "FUND001" in transactions[0]["description"]


def test_query_transactions_without_token(base_url):
    response = requests.get(f"{base_url}/api/transactions", timeout=3)

    assert response.status_code == 401
    assert response.json()["message"] == "unauthorized"
