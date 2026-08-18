"""신뢰 크리에이터 배지 판정(갭 #81) — 흩어진 신호(인증·실적·응답·분쟁)의 통합.

순수 함수 — 기준값은 core/config가 소유하고 인자로 주입받는다(vetting_check와 같은 원칙).
"가짜 인플루언서 검증은 브랜드 몫"이라는 레퍼런스 비판(§8)의 반대편: 플랫폼이 검증 신호를
묶어 판정한다. 감점 신호(무응답 만료·분쟁 패소)는 배지 판정에만 쓰고 공개 수치로 노출하지
않는다 — 신규·소규모 크리에이터를 공개적으로 깎지 않기 위함이다.
"""

from __future__ import annotations


def is_trusted_creator(
    verified_channels: int,
    completed_orders: int,
    accept_expired_orders: int,
    dispute_refund_orders: int,
    *,
    min_verified_channels: int,
    min_completed_orders: int,
) -> bool:
    """스크린샷 인증 채널·완료 거래가 기준 이상이고, 무응답 만료·분쟁 패소가 없을 때."""
    if verified_channels < min_verified_channels:
        return False
    if completed_orders < min_completed_orders:
        return False
    if accept_expired_orders > 0:
        return False
    return dispute_refund_orders == 0
