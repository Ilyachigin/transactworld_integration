from pydantic import BaseModel


class InnerParams(BaseModel):
    amount: int

class PaymentInfo(BaseModel):
    gateway_amount: int
    token: str
    gateway_token: str
    gateway_currency: str


class SettingsInfo(BaseModel):
    username: str
    partner_id: str
    member_id: str
    secure_key: str


class RefundRequest(BaseModel):
    params: InnerParams
    payment: PaymentInfo
    settings: SettingsInfo
