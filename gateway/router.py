from fastapi import APIRouter

from schemas.payment import PaymentRequest
from schemas.callback import GatewayCallback
from schemas.refund import RefundRequest
from schemas.status import GatewayStatus
from gateway.handler import (
    handle_pay,
    handle_status,
    handle_callback,
    handle_refund
)


router = APIRouter()


@router.post("/pay")
async def pay(data: PaymentRequest):
    return await handle_pay(data)

@router.post("/refund")
async def pay(data: RefundRequest):
    return await handle_refund(data)


@router.post("/status")
async def status(data: GatewayStatus):
    return await handle_status(data)


@router.post("/callback")
async def callback(data: GatewayCallback):
    return await handle_callback(data)

