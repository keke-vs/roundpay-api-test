import requests


def test_frontend_home_page_available(base_url):
    response = requests.get(base_url, timeout=3)

    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert "个人支付业务演示系统" in response.text
    assert 'id="auth-screen"' in response.text
    assert 'id="app-screen" class="app-shell hidden"' in response.text
    assert 'id="login-form"' in response.text
    assert 'id="transaction-table"' in response.text


def test_frontend_static_assets_available(base_url):
    css = requests.get(f"{base_url}/static/app.css", timeout=3)
    script = requests.get(f"{base_url}/static/app.js", timeout=3)

    assert css.status_code == 200
    assert "text/css" in css.headers["Content-Type"]
    assert ".summary-grid" in css.text
    assert script.status_code == 200
    assert "application/javascript" in script.headers["Content-Type"]
    assert "/api/account" in script.text
    assert "/api/transactions" in script.text
