import socket
import threading

import pytest
import requests

from api.roundpay_server import create_server


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def base_url():
    port = free_port()
    server = create_server(port=port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture()
def auth_headers(base_url):
    response = requests.post(
        f"{base_url}/api/login",
        json={"username": "alice", "password": "123456"},
        timeout=3,
    )
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}

