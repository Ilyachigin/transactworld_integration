from pydantic import BaseModel
from typing import Dict, Any, Union


class StatusParams(BaseModel):
    gateway_token: str
    token: str


class SettingsInfo(BaseModel):
    username: str
    partner_id: str
    member_id: str
    secure_key: str


class GatewayStatus(BaseModel):
    settings: SettingsInfo
    refund: Union[Dict[str, Any], None] = None
    payment: StatusParams
