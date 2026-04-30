SUCCESS_SCHEMA = {
    "type": "object",
    "required": ["code", "message", "data"],
    "properties": {
        "code": {"type": "number"},
        "message": {"type": "string"},
        "data": {"type": "object"},
    },
}

LOGIN_SCHEMA = {
    "type": "object",
    "required": ["code", "message", "data"],
    "properties": {
        "code": {"const": 0},
        "message": {"type": "string"},
        "data": {
            "type": "object",
            "required": ["token", "account", "nickname"],
            "properties": {
                "token": {"type": "string"},
                "account": {"type": "string"},
                "nickname": {"type": "string"},
            },
        },
    },
}

TRANSFER_SCHEMA = {
    "type": "object",
    "required": ["code", "message", "data"],
    "properties": {
        "code": {"const": 0},
        "message": {"type": "string"},
        "data": {
            "type": "object",
            "required": [
                "requestId",
                "fromAccount",
                "toAccount",
                "amount",
                "fromBalance",
                "toBalance",
            ],
        },
    },
}

