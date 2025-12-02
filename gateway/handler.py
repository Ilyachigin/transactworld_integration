from fastapi import Response
from datetime import datetime, timedelta, timezone

import config
from client.http import send_request
from schemas.payment import PaymentRequest
from schemas.callback import GatewayCallback
from schemas.status import GatewayStatus
from schemas.refund import RefundRequest
from utils.logger import logger
from gateway.builder import (
    gateway_body,
    gateway_auth_body,
    gateway_status_body,
    gateway_auth_response,
    gateway_callback_body,
    gateway_refund_body,
    headers_param,
    database_insert,
    response_handler,
    merchant_token_encrypt,
    callback_jwt,
    db
)


async def handle_pay(data: PaymentRequest):
    raw_data = data.model_dump(exclude_none=True)
    logger.info(f"Business request body: {raw_data}")

    bearer_token = raw_data.get("payment", {}).get("merchant_private_key")
    settings = raw_data.get("settings", {})

    auth_token = db.get_auth_token(settings.get("username"))
    auth_data = None
    if not auth_token:
        auth_data, auth_token = handle_auth_token(settings)

    gateway_payload = gateway_body(raw_data)
    url = f"{config.GATEWAY_URL}/payments"
    headers = headers_param(auth_token)

    response = send_request('POST', url, headers, gateway_payload)
    database_insert(response.get('response'), bearer_token)

    pay_data = {
        "kind": "pay",
        "url": url,
        "body": gateway_payload,
        "response": response
    }
    return response_handler("pay", auth_data, pay_data)


async def handle_status(data: GatewayStatus):
    raw_data = data.model_dump(exclude_none=True)
    logger.info(f"Business request body: {raw_data}")

    settings = raw_data.get("settings", {})
    if raw_data.get("refund"):
        gateway_token = raw_data.get("refund").get("token")
    else:
        gateway_token = raw_data.get("payment").get("token")

    auth_token = db.get_auth_token(settings.get("username"))
    auth_data = None
    if not auth_token:
        auth_data, auth_token = handle_auth_token(settings)


    url = f"{config.GATEWAY_URL}/payments/{gateway_token}"
    gateway_payload = gateway_status_body(raw_data)
    headers = headers_param(auth_token)

    response = send_request('POST', url, headers, gateway_payload)

    status_data = {
        "kind": "status",
        "url": url,
        "body": gateway_payload,
        "response": response
    }
    return response_handler('status', auth_data, status_data)


async def handle_refund(data: RefundRequest):
    raw_data = data.model_dump(exclude_none=True)
    logger.info(f"Business request body: {raw_data}")

    # settings = raw_data.get("settings", {})
    # gateway_token = raw_data.get("payment").get("gateway_token")
    #
    # auth_token = db.get_auth_token(settings.get("username"))
    # auth_data = None
    # if not auth_token:
    #     auth_data, auth_token = handle_auth_token(settings)
    #
    # url = f"{config.GATEWAY_URL}/refund/{gateway_token}"
    # gateway_payload = gateway_refund_body(raw_data)
    # headers = headers_param(auth_token)

    #response = send_request('POST', url, headers, gateway_payload)

    # refund_data = {
    #     "kind": "refund",
    #     "url": url,
    #     "body": gateway_payload,
    #     "response": response
    # }
    return response_handler('refund', auth_data=None, pay_data=raw_data)


async def handle_callback(data: GatewayCallback):
    raw_data = data.model_dump(exclude_none=True)
    logger.info(f"Gateway callback body: {raw_data}")
    bearer_token = db.get_token(raw_data.get("paymentId"))
    gateway_token, callback_body = gateway_callback_body(raw_data)

    if bearer_token:
        secure_data = merchant_token_encrypt(bearer_token, config.SIGN_KEY)
        jwt_payload = {
            **callback_body,
            "secure": secure_data
        }
        jwt_token = callback_jwt(jwt_payload, config.SIGN_KEY)
        callback_headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

        url = f"{config.BUSINESS_URL}/callbacks/v2/gateway_callbacks/{gateway_token}"
        send_request('POST', url, callback_headers, callback_body, json=True)
        return Response(content="ok", status_code=200)
    else:
        return Response(content="ok", status_code=404)


def handle_auth_token(settings: dict) -> tuple[dict[str, str | dict], str]:
    gateway_payload = gateway_auth_body(settings)
    url = f"{config.GATEWAY_URL}/authToken"
    headers = headers_param()

    response = send_request('POST', url, headers, gateway_payload)
    auth_token = gateway_auth_response(response)
    if auth_token:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=55) # Auth token valid for ~1 hour
        db.upsert_auth_token(settings.get("username"), auth_token, expires_at)

    auth_data = {
        "kind": "auth",
        "url": url,
        "body": gateway_payload,
        "response": response
    }

    return auth_data, auth_token

