# 接口说明

本文档记录圆小付 mock 服务当前提供的接口。接口字段只保留测试项目需要用到的部分，没有按完整生产接口设计。

## 1. 登录

| 项目 | 内容 |
| --- | --- |
| URL | `/api/login` |
| Method | POST |
| 是否鉴权 | 否 |
| 主要测试点 | 必填参数、密码错误、Token 返回 |

请求示例：

```json
{
  "username": "alice",
  "password": "123456"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "token-alice",
    "account": "62220001",
    "nickname": "Alice"
  }
}
```

## 2. 转账

| 项目 | 内容 |
| --- | --- |
| URL | `/api/transfer` |
| Method | POST |
| 是否鉴权 | 是 |
| 主要测试点 | 金额边界、余额变化、重复提交、未登录访问 |

请求示例：

```json
{
  "toAccount": "62220002",
  "amount": 88.66,
  "requestId": "REQ-001"
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| toAccount | 收款账号 |
| amount | 转账金额，必须大于 0，最多两位小数 |
| requestId | 请求唯一编号，用于处理重复提交 |

## 3. 修改个人信息

| 项目 | 内容 |
| --- | --- |
| URL | `/api/profile` |
| Method | PATCH |
| 是否鉴权 | 是 |
| 主要测试点 | 手机号格式、昵称修改、未登录访问 |

请求示例：

```json
{
  "nickname": "Alice Test",
  "mobile": "13900000001"
}
```

## 4. 查询基金列表

| 项目 | 内容 |
| --- | --- |
| URL | `/api/funds?page=1&pageSize=10` |
| Method | GET |
| 是否鉴权 | 否 |
| 主要测试点 | 分页参数、返回字段、列表数据 |

返回字段中包含 `page`、`pageSize`、`total` 和 `items`。

## 5. 购买基金

| 项目 | 内容 |
| --- | --- |
| URL | `/api/fund/buy` |
| Method | POST |
| 是否鉴权 | 是 |
| 主要测试点 | 基金状态、起购金额、余额不足、交易状态 |

请求示例：

```json
{
  "fundId": "FUND001",
  "amount": 100
}
```

购买成功后返回交易号、基金编号、购买金额、账户余额和交易状态。

