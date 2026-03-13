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
    customer: Optional[CustomerParams]
    pan: Optional[str] = None
    expires: Optional[str] = None
    holder: Optional[str] = None
    cvv: Optional[str] = None
    browser: Optional[dict]
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    ip: Optional[str] = None
    birthday: Optional[str] = None
    extra_return_param: str


class PaymentInfo(BaseModel):
    ip: str
    token: str
    card_brand_name: Optional[str] = None
    gateway_amount: int
    gateway_currency: str
    merchant_private_key: str


class SettingsInfo(BaseModel):
    method: Optional[str]
    username: str
    partner_id: str
    member_id: str
    secure_key: str
    apple_terminal_id: Optional[str]
    google_terminal_id: Optional[str]
    visa_terminal_id: Optional[str]
    mc_terminal_id: Optional[str]


class PaymentRequest(BaseModel):
    params: Optional[InnerParams]
    payment: PaymentInfo
    settings: SettingsInfo
    processing_url: str
    method_name: Optional[str]
