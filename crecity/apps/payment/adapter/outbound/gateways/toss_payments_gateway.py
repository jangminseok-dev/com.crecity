import base64
import logging

import httpx

from payment.app.exceptions import PaymentConfirmError
from payment.app.ports.output.payment_gateway import PaymentGateway

_API_BASE = "https://api.tosspayments.com"

logger = logging.getLogger(__name__)


class TossPaymentsGateway(PaymentGateway):
    """토스페이먼츠 코어 API — 시크릿 키 Basic 인증(§7-3: 포트 격리, 교체 가능)."""

    def __init__(self, secret_key: str) -> None:
        # Basic base64("<secret_key>:") — 토스 인증 규격
        token = base64.b64encode(f"{secret_key}:".encode()).decode()
        self._headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    async def confirm(self, payment_key: str, pg_order_id: str, amount_krw: int) -> None:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{_API_BASE}/v1/payments/confirm",
                headers=self._headers,
                json={"paymentKey": payment_key, "orderId": pg_order_id, "amount": amount_krw},
            )
        if response.status_code != 200:
            message = response.json().get("message", f"HTTP {response.status_code}")
            raise PaymentConfirmError(f"결제 승인 실패: {message}")

    async def cancel(self, payment_key: str, reason: str) -> None:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{_API_BASE}/v1/payments/{payment_key}/cancel",
                headers=self._headers,
                json={"cancelReason": reason},
            )
        if response.status_code != 200:
            message = response.json().get("message", f"HTTP {response.status_code}")
            logger.error("토스 결제 취소 실패: paymentKey=%s — %s", payment_key, message)
            raise PaymentConfirmError(f"결제 취소 실패: {message}")
