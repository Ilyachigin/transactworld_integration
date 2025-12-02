from pydantic import BaseModel, ConfigDict
from typing import Optional


class Result(BaseModel):
    code: str
    description: str


class Customer(BaseModel):
    email: Optional[str] = None
    id: Optional[str] = None


class Card(BaseModel):
    bin: Optional[str] = None
    lastFourDigits: Optional[str] = None
    last4Digits: Optional[str] = None
    expiryMonth: Optional[str] = None
    expiryYear: Optional[str] = None


class GatewayCallback(BaseModel):
    model_config = ConfigDict(extra="allow")
    paymentId: str
    status: str
    transactionStatus: str
    paymentBrand: str
    paymentMode: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    amount: str
    currency: str
    descriptor: Optional[str] = None
    merchantTransactionId: str
    remark: Optional[str] = None
    tmpl_amount: Optional[str] = None
    tmpl_currency: Optional[str] = None
    checksum: Optional[str] = None
    result: Optional[Result] = None
    customer: Optional[Customer] = None
    card: Optional[Card] = None
    timestamp: Optional[str] = None
    eci: Optional[str] = None
    bankReferenceId: Optional[str] = None
    terminalId: Optional[str] = None