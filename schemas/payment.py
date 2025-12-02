from pydantic import BaseModel
from typing import Optional


class CustomerParams(BaseModel):
    email: str
    first_name: str
    last_name: str
    country: str
    city: str
    state: str
    postcode: str
    address: str
    phone: str


class InnerParams(BaseModel):
    customer: CustomerParams
    extra_return_param: str


class PaymentInfo(BaseModel):
    token: str
    gateway_amount: int
    gateway_currency: str
    merchant_private_key: str


class SettingsInfo(BaseModel):
    method: str
    username: str
    partner_id: str
    member_id: str
    secure_key: str
    apple_terminal_id: str
    google_terminal_id: str


class PaymentRequest(BaseModel):
    params: Optional[InnerParams]
    payment: PaymentInfo
    settings: SettingsInfo
    processing_url: str
    method_name: Optional[str]
