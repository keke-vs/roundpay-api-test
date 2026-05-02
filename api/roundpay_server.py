import json
import re
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class RoundPayState:
    def __init__(self):
        self.users = {
            "alice": {
                "password": "123456",
                "token": "token-alice",
                "account": "62220001",
                "nickname": "Alice",
                "mobile": "13800000001",
            },
            "bob": {
                "password": "123456",
                "token": "token-bob",
                "account": "62220002",
                "nickname": "Bob",
                "mobile": "13800000002",
            },
        }
        self.balances = {
            "62220001": 5000.00,
            "62220002": 1200.00,
        }
        self.transfer_requests = {}
        self.transactions = []
        self.transaction_sequence = 1000
        self.funds = {
            "FUND001": {"name": "稳健理财A", "status": "OPEN", "minAmount": 10.00},
            "FUND002": {"name": "指数增强B", "status": "CLOSED", "minAmount": 100.00},
        }

    def user_by_token(self, token):
        for username, user in self.users.items():
            if user["token"] == token:
                return username, user
        return None, None

    def add_transaction(self, account, txn_type, amount, description, status="SUCCESS"):
        self.transaction_sequence += 1
        transaction = {
            "transactionId": f"TXN{self.transaction_sequence}",
            "account": account,
            "type": txn_type,
            "amount": amount,
            "description": description,
            "status": status,
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.transactions.insert(0, transaction)
        return transaction


STATE = RoundPayState()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
STATIC_CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".html": "text/html; charset=utf-8",
}


def make_response(code=0, message="success", data=None):
    return {
        "code": code,
        "message": message,
        "data": data or {},
    }


class RoundPayHandler(BaseHTTPRequestHandler):
    server_version = "RoundPayMock/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.write_file(FRONTEND_DIR / "index.html")
            return
        if parsed.path.startswith("/static/"):
            self.handle_static(parsed.path)
            return
        if parsed.path == "/api/account":
            self.handle_account()
            return
        if parsed.path == "/api/funds":
            self.handle_funds(parsed)
            return
        if parsed.path == "/api/transactions":
            self.handle_transactions(parsed)
            return
        self.write_json(404, make_response(404, "not found"))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/login":
            self.handle_login()
            return
        if parsed.path == "/api/transfer":
            self.handle_transfer()
            return
        if parsed.path == "/api/fund/buy":
            self.handle_fund_buy()
            return
        self.write_json(404, make_response(404, "not found"))

    def do_PATCH(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/profile":
            self.handle_profile()
            return
        self.write_json(404, make_response(404, "not found"))

    def handle_login(self):
        body = self.read_body()
        username = body.get("username")
        password = body.get("password")
        user = STATE.users.get(username)

        if not username or not password:
            self.write_json(400, make_response(400, "username and password are required"))
            return
        if not user or user["password"] != password:
            self.write_json(401, make_response(401, "username or password is wrong"))
            return

        self.write_json(200, make_response(data={
            "token": user["token"],
            "account": user["account"],
            "nickname": user["nickname"],
        }))

    def handle_transfer(self):
        username, user = self.current_user()
        if not user:
            return

        body = self.read_body()
        to_account = body.get("toAccount")
        amount = body.get("amount")
        request_id = body.get("requestId")

        if not request_id:
            self.write_json(400, make_response(400, "requestId is required"))
            return
        if request_id in STATE.transfer_requests:
            self.write_json(200, make_response(data=STATE.transfer_requests[request_id]))
            return
        if to_account not in STATE.balances:
            self.write_json(400, make_response(400, "target account does not exist"))
            return
        if not isinstance(amount, (int, float)) or amount <= 0:
            self.write_json(400, make_response(400, "amount must be greater than 0"))
            return
        if round(amount, 2) != amount:
            self.write_json(400, make_response(400, "amount supports up to two decimal places"))
            return

        from_account = user["account"]
        if STATE.balances[from_account] < amount:
            self.write_json(400, make_response(400, "insufficient balance"))
            return

        STATE.balances[from_account] = round(STATE.balances[from_account] - amount, 2)
        STATE.balances[to_account] = round(STATE.balances[to_account] + amount, 2)
        result = {
            "requestId": request_id,
            "fromAccount": from_account,
            "toAccount": to_account,
            "amount": amount,
            "fromBalance": STATE.balances[from_account],
            "toBalance": STATE.balances[to_account],
        }
        result["transactionId"] = STATE.add_transaction(
            from_account,
            "TRANSFER_OUT",
            -amount,
            f"转账至 {to_account}",
        )["transactionId"]
        STATE.add_transaction(
            to_account,
            "TRANSFER_IN",
            amount,
            f"收到 {from_account} 转账",
        )
        STATE.transfer_requests[request_id] = result
        self.write_json(200, make_response(data=result))

    def handle_profile(self):
        username, user = self.current_user()
        if not user:
            return

        body = self.read_body()
        nickname = body.get("nickname", user["nickname"])
        mobile = body.get("mobile", user["mobile"])

        if not re.fullmatch(r"1[3-9]\d{9}", str(mobile)):
            self.write_json(400, make_response(400, "mobile format is invalid"))
            return

        user["nickname"] = nickname
        user["mobile"] = mobile
        self.write_json(200, make_response(data={
            "username": username,
            "nickname": user["nickname"],
            "mobile": user["mobile"],
        }))

    def handle_account(self):
        username, user = self.current_user()
        if not user:
            return

        account = user["account"]
        self.write_json(200, make_response(data={
            "username": username,
            "account": account,
            "nickname": user["nickname"],
            "mobile": user["mobile"],
            "balance": STATE.balances[account],
        }))

    def handle_transactions(self, parsed):
        username, user = self.current_user()
        if not user:
            return

        query = parse_qs(parsed.query)
        limit = int(query.get("limit", ["20"])[0])
        account = user["account"]
        items = [
            transaction
            for transaction in STATE.transactions
            if transaction["account"] == account
        ][:limit]
        self.write_json(200, make_response(data={
            "total": len(items),
            "items": items,
        }))

    def handle_funds(self, parsed):
        query = parse_qs(parsed.query)
        page = int(query.get("page", ["1"])[0])
        page_size = int(query.get("pageSize", ["10"])[0])
        all_funds = [
            {"fundId": fund_id, **fund}
            for fund_id, fund in STATE.funds.items()
        ]
        start = (page - 1) * page_size
        end = start + page_size
        self.write_json(200, make_response(data={
            "page": page,
            "pageSize": page_size,
            "total": len(all_funds),
            "items": all_funds[start:end],
        }))

    def handle_fund_buy(self):
        username, user = self.current_user()
        if not user:
            return

        body = self.read_body()
        fund_id = body.get("fundId")
        amount = body.get("amount")
        fund = STATE.funds.get(fund_id)

        if not fund:
            self.write_json(400, make_response(400, "fund does not exist"))
            return
        if fund["status"] != "OPEN":
            self.write_json(400, make_response(400, "fund is not available"))
            return
        if not isinstance(amount, (int, float)) or amount < fund["minAmount"]:
            self.write_json(400, make_response(400, "amount is less than minimum purchase amount"))
            return

        account = user["account"]
        if STATE.balances[account] < amount:
            self.write_json(400, make_response(400, "insufficient balance"))
            return

        STATE.balances[account] = round(STATE.balances[account] - amount, 2)
        transaction = STATE.add_transaction(
            account,
            "FUND_BUY",
            -amount,
            f"购买 {fund_id} {fund['name']}",
        )
        self.write_json(200, make_response(data={
            "tradeId": transaction["transactionId"],
            "fundId": fund_id,
            "amount": amount,
            "balance": STATE.balances[account],
            "status": "SUCCESS",
        }))

    def current_user(self):
        auth = self.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "", 1)
        username, user = STATE.user_by_token(token)
        if not user:
            self.write_json(401, make_response(401, "unauthorized"))
            return None, None
        return username, user

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def write_json(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_static(self, path):
        relative_path = path.removeprefix("/static/").strip("/")
        if not relative_path:
            self.write_json(404, make_response(404, "not found"))
            return

        target = (FRONTEND_DIR / relative_path).resolve()
        if FRONTEND_DIR.resolve() not in target.parents:
            self.write_json(403, make_response(403, "forbidden"))
            return
        self.write_file(target)

    def write_file(self, path):
        if not path.exists() or not path.is_file():
            self.write_json(404, make_response(404, "not found"))
            return

        content = path.read_bytes()
        content_type = STATIC_CONTENT_TYPES.get(path.suffix, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        return


def create_server(host="127.0.0.1", port=8000):
    global STATE
    STATE = RoundPayState()
    return ThreadingHTTPServer((host, port), RoundPayHandler)


if __name__ == "__main__":
    server = create_server()
    try:
        if sys.stdout:
            print("RoundPay mock server running at http://127.0.0.1:8000")
    except OSError:
        pass
    server.serve_forever()
