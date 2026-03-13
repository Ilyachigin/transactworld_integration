import copy
import json
import jwt
import base64
import hashlib
from datetime import datetime
from typing import Dict, Union, Any
from decimal import Decimal, ROUND_HALF_UP

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

import config
from utils.db import DatabaseStorage


db = DatabaseStorage()

card_brand = {
    "Visa": "VISA",
    "MasterCard": "MC"
}


def gateway_body(business_data: Dict) -> Dict:
    payment_body = business_data.get("payment", {})
    params_body = business_data.get("params", {})

    is_card = bool(params_body.get("pan"))

    if params_body.get("pan"):
        payment_brand = card_brand.get(payment_body.get("card_brand_name"))
        payment_mode = "CC"
    else:
        extra_return_param = params_body.get("extra_return_param")
        payment_brand = extra_return_param or business_data.get("settings", {}).get("method")
        payment_mode = "EW"

    request_body = {
        **authentication_params(business_data, payment_brand),
        **shipping_params(business_data, is_card),
        **customer_params(business_data, is_card),
        "paymentMode": payment_mode,
        "paymentType": "DB",
        "paymentBrand": payment_brand,
        "merchantTransactionId": payment_body.get("token"),
        "amount": amount_convert(payment_body.get('gateway_amount')),
        "currency": payment_body.get("gateway_currency"),
        "merchantRedirectUrl": business_data.get("processing_url"),
        "notificationUrl": f"{config.BASE_URL}/callback"
    }
    if is_card:
        request_body.update(browser_params(params_body))
        request_body.update(card_params(params_body))

    return request_body

def gateway_status_body(business_data: Dict) -> Dict:
    return {
        "authentication.memberId": business_data.get("settings", {}).get("member_id"),
        "authentication.checksum": check_sum(business_data, status=True), #recheck
        "paymentType": "IN",
        "idType": "MID",
        "merchantTransactionId":  business_data.get("payment", {}).get("token")
    }


def gateway_refund_body(business_data: dict) -> dict:
    request_body = business_data.get("payment", {})
    refund_amount = business_data.get("params").get("amount")

    return {
        "authentication.memberId": business_data.get("settings", {}).get("member_id"),
        "authentication.checksum": check_sum(business_data, refund=True),
        "paymentType": "RF",
        "amount": amount_convert(refund_amount),
        "paymentId": request_body.get("gateway_token")
    }


def gateway_callback_body(data: dict) -> tuple[str | None, dict[str, str | int]]:
    token = data.get("paymentId")
    status = status_mapping(data.get("transactionStatus"))

    logs_response = {
        "response": "ok",
        "duration": 0.01, # dummy value for duration
        "status_code": 200
    }

    callback_body = {
        "kind": "callback",
        "url": f"{config.BASE_URL}/callback",
        "body": data,
        "status": status,
        "response": logs_response,
        "currency": data.get("currency"),
        "amount": amount_convert(data.get("amount"), reverse=True)
    }

    callback_body["logs"] = response_logs_params(auth_data=None, pay_data=callback_body)

    if status == "declined":
        callback_body["reason"] = data.get("result", {}).get("description") or "Transaction declined"

    return token, callback_body


def gateway_auth_body(data: dict) -> dict:
    return {
        "authentication.partnerId": data.get("partner_id"),
        "authentication.sKey": data.get("secure_key"),
        "merchant.username": data.get("username")
    }


def gateway_pay_response(auth_data: dict, pay_data: dict) -> Dict:
    response_body = pay_data.get("response", {}).get("response")
    token = response_body.get("paymentId")
    processing_url = response_body.get("redirect", {}).get("url")
    transaction_status = status_mapping(response_body.get("transactionStatus"))

    return {
        "status": "OK",
        "gateway_token": token,
        "result": transaction_status,
        "processing_url": processing_url,
        "redirect_request": response_redirect_params(response_body),
        "logs": response_logs_params(auth_data, pay_data)
    }


def gateway_auth_response(auth_data: dict) -> str:
    response_body = auth_data.get("response", {})

    return response_body.get("AuthToken", "")


def gateway_status_response(auth_data: dict, pay_data: dict):
    gateway_response = pay_data.get("response", {}).get("response", {})
    amount = amount_convert(gateway_response.get("amount"), reverse=True)
    currency = gateway_response.get("currency")
    status = status_mapping(gateway_response.get("transactionStatus"))
    description = gateway_response.get("result", {}).get("description")

    return {
        "result": "OK",
        "status": status,
        "details": description or status,
        "amount": amount ,
        "currency": currency,
        "logs": response_logs_params(auth_data, pay_data)
    }


def gateway_decline_response(auth_data: dict, pay_data: dict | str):
    request_body = pay_data.get("body", {})
    gateway_response = pay_data.get("response", {}).get("response", {})
    reason = gateway_response.get("result", {}).get("description") or "Transaction declined"
    amount = amount_convert(request_body.get("amount"), reverse=True)

    result = {
        "result": "OK",
        "status": 'declined',
        "details":  reason,
        "amount": amount,
        "logs": response_logs_params(auth_data, pay_data)
    }
    return result


def customer_params(business_data: dict, is_card: bool) -> Dict:
    params_data = business_data.get("params", {})
    request_body = params_data if is_card else params_data.get("customer")

    phone = request_body.get("phone", "")

    params = {
        "customer.telnocc": phone[:3] if phone.startswith("+") else "+" + phone[:2],
        "customer.phone": phone[3:] if phone.startswith("+") else phone[2:],
        "customer.email": request_body.get("email"),
        "customer.givenName": request_body.get("first_name"),
        "customer.surname": request_body.get("last_name"),
        "customer.ip": request_body.get("ip") or business_data.get("payment", {}).get("ip"),
        "customer.birthDate": request_body.get("birthday"),

    }

    return clean_data(params)


def shipping_params(business_data: dict, is_card: bool) -> Dict:
    params_data = business_data.get("params", {})
    request_body = params_data if is_card else params_data.get("customer")

    params = {
        "shipping.country": request_body.get("country"),
        "shipping.city": request_body.get("city"),
        "shipping.state": request_body.get("state"),
        "shipping.postcode": request_body.get("postcode"),
        "shipping.street1": request_body.get("address"),
        "shipping.givenName": request_body.get("first_name"),
        "shipping.surname": request_body.get("last_name")
    }

    return clean_data(params)


def authentication_params(business_data: dict, payment_brand: str) -> Dict:
    settings_body = business_data.get("settings", {})
    terminal_brand = None

    if payment_brand.upper() == "APPLEPAY":
        terminal_brand = settings_body.get("apple_terminal_id")
    elif payment_brand.upper() == "GOOGLEPAY":
        terminal_brand = settings_body.get("google_terminal_id")
    elif payment_brand.upper() == "VISA":
        terminal_brand = settings_body.get("visa_terminal_id")
    elif payment_brand.upper() == "MC":
        terminal_brand = settings_body.get("mc_terminal_id")

    params = {
        "authentication.memberId": settings_body.get("member_id"),
        "authentication.checksum": check_sum(business_data),
        "authentication.terminalId": terminal_brand
    }

    return clean_data(params)


def browser_params(data: dict) -> Dict:
    browser_data = data.get("browser", {})

    params = {
        "deviceDetails.browserAcceptHeader": browser_data.get("accept_header"),
        "deviceDetails.browserColorDepth": browser_data.get("color_depth"),
        "deviceDetails.browserLanguage": browser_data.get("language", "en-US")[:5],
        "deviceDetails.browserScreenHeight": browser_data.get("screen_height"),
        "deviceDetails.browserScreenWidth": browser_data.get("screen_width"),
        "deviceDetails.browserTimezoneOffset": browser_data.get("tz"),
        "deviceDetails.user_Agent": browser_data.get("user_agent"),
        "deviceDetails.browserJavaEnabled": bool(browser_data.get("java_enabled"))
    }

    return clean_data(params)


def card_params(data: dict) -> Dict:
    month, year = data.get("expires").split("/")
    card_number = data.get("pan", "").replace("-", "")

    params = {
        "card.number": card_number,
        "card.expiryMonth": int(month),
        "card.expiryYear": int(year),
        "card.cvv": data.get("cvv")
    }

    return clean_data(params)


def check_sum(business_data: dict, status=False, refund=False) -> str:
    settings_body = business_data.get("settings")
    payment_body = business_data.get("payment")

    member_id = settings_body.get("member_id")
    secure_key = settings_body.get("secure_key")
    transaction_token = payment_body.get("token")

    if refund:
        gateway_amount = business_data.get("params", {}).get("amount")
        transaction_token = payment_body.get("gateway_token")
    else:
        gateway_amount = payment_body.get("gateway_amount")

    amount = None
    if gateway_amount is not None:
        amount = amount_convert(gateway_amount)
    if status:
        # <memberId>|<secureKey>|<paymentId>
        raw = f"{member_id}|{secure_key}|{transaction_token}"
    else:
        # <memberId>|<secureKey>|<merchantTransactionId or paymentId>|<amount>
        raw = f"{member_id}|{secure_key}|{transaction_token}|{amount}"

    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def response_redirect_params(redirect_request: dict) -> Dict:
    redirect_body = redirect_request.get("redirect", {})
    redirect_url = redirect_body.get("url")
    redirect_method = (redirect_body.get("method") or "post").lower()
    redirect_params = redirect_body.get("parameters")

    redirect_response = {
        "url": redirect_url,
        "type": redirect_method
    }
    if redirect_params:
        redirect_response["params"] = {item["name"]: item["value"] for item in redirect_params}

    return redirect_response


def response_logs_params(auth_data, pay_data) -> list | dict:
    return [
        {
            "gateway": "Transactworld",
            "request": {
                "url": data.get("url"),
                "params": mask_data(data.get("body"))
            },
            "status": data.get("response", {}).get("status_code"),
            "response": data.get("response", {}).get("response"),
            "kind": data.get("kind"),
            "created_at": datetime.now().isoformat(),
            "duration": data.get("response", {}).get("duration")
        }
        for data in (auth_data, pay_data)
        if data is not None
    ]


def status_mapping(status: str) -> str:
    """ Y – Successfully processed
        N – Failed
        P – Pending
        3D – Pending for 3D authentication
        C – Cancelled"""
    mapping = {
        "approved": ["Y"],
        "declined": ["C", "N"]
    }

    for key, values in mapping.items():
        if status in values:
            return key

    return "pending"


def callback_jwt(callback_body: dict, sign_key: str) -> str:
    return jwt.encode(
        payload=callback_body,
        key=sign_key,
        algorithm="HS512"
    )


def merchant_token_encrypt(merchant_token: str, sign_key: str) -> dict:
    def pad(data: bytes) -> bytes:
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len] * pad_len)

    key = sign_key.encode('utf-8')[:32]
    iv = get_random_bytes(16)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(merchant_token.encode('utf-8'))
    encrypted = cipher.encrypt(padded_data)

    return {
        "encrypted_data": base64.b64encode(encrypted).decode('utf-8'),
        "iv_value": base64.b64encode(iv).decode('utf-8')
    }


def headers_param(auth_token: str = None) -> dict:
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    if auth_token:
        headers["AuthToken"] = auth_token

    return headers


def response_handler(request_type, auth_data: dict | None, pay_data: dict):
    gateway_response = pay_data.get("response", {}).get("response", {})

    if pay_data["response"].get("status") == "ok" and gateway_response.get("paymentId") not in ("-", None):
        if request_type in ["pay", "refund"]:
            return gateway_pay_response(auth_data, pay_data)
        elif request_type == "status":
            return gateway_status_response(auth_data, pay_data)
        return None
    else:
        return gateway_decline_response(auth_data, pay_data)


def database_insert(data: dict, bearer_token: str):
    token = data.get("paymentId")
    if token:
        db.insert_token(token, bearer_token)
        db.delete_old_tokens()


def clean_data(params: dict) -> dict:
    return {k: v for k, v in params.items() if v is not None and v != ""}


def mask_data(data: Union[dict, str]) -> dict | None | Any:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data
    if not data:
        return data

    masked = copy.deepcopy(data)

    if masked.get("card.number"):
        pan = str(masked["card.number"]).replace(" ", "")
        masked["card.number"] = f"{pan[:6]}******{pan[-4:]}" if len(pan) >= 10 else "************"

    if masked.get("card.cvv"):
        masked["card.cvv"] = "***"

    return masked


def amount_convert(value, reverse: bool = False) -> int | Decimal:
    if not reverse:
        return (Decimal(value) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return int((Decimal(str(value)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

