import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
        self.funds = {
            "FUND001": {"name": "稳健理财A", "status": "OPEN", "minAmount": 10.00},
            "FUND002": {"name": "指数增强B", "status": "CLOSED", "minAmount": 100.00},
        }

    def user_by_token(self, token):
        for username, user in self.users.items():
            if user["token"] == token:
                return username, user
        return None, None


STATE = RoundPayState()


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
        if parsed.path == "/api/funds":
            self.handle_funds(parsed)
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
        self.write_json(200, make_response(data={
            "tradeId": f"T{account}{int(amount * 100)}",
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

    def log_message(self, format, *args):
        return


def create_server(host="127.0.0.1", port=8000):
    return ThreadingHTTPServer((host, port), RoundPayHandler)


if __name__ == "__main__":
    server = create_server()
    print("RoundPay mock server running at http://127.0.0.1:8000")
    server.serve_forever()

