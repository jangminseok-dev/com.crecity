"""자가 입력 지표 이상치 판정(갭 #82) — 순수 함수(기준값은 core/config 소유, 주입).

"검증은 브랜드의 실사 몫"이라는 레퍼런스 비판(§8)의 반대편: 의심스러운 자가 입력을
플랫폼이 자동으로 골라 운영자 재검토 큐에 올린다. **판정은 플래그일 뿐 노출·거래를
막지 않는다** — 오탐으로 정상 크리에이터를 벌하지 않기 위함이다(광고 표기 검수와 같은 원칙).
"""

from __future__ import annotations


def detect_anomaly(
    previous_followers: int | None,
    new_followers: int,
    engagement_permille: int | None,
    *,
    surge_multiplier: int,
    engagement_floor_followers: int,
    max_engagement_permille: int,
) -> str | None:
    """이상치면 사유 문구, 정상이면 None.

    - 급증: 재제출 값이 직전 값의 surge_multiplier배 이상(첫 제출은 비교 대상 없음).
    - 고참여율: 대형 계정(팔로워 ≥ floor)인데 참여율이 상한을 넘는 경우 —
      규모가 클수록 참여율은 낮아지는 일반 경향과 어긋난다.
    """
    if (
        previous_followers is not None
        and previous_followers > 0
        and new_followers >= previous_followers * surge_multiplier
    ):
        return f"팔로워 급증: {previous_followers:,} → {new_followers:,}"
    if (
        engagement_permille is not None
        and new_followers >= engagement_floor_followers
        and engagement_permille > max_engagement_permille
    ):
        return (
            f"대형 계정 고참여율: 팔로워 {new_followers:,} · "
            f"참여율 {engagement_permille / 10:.1f}%"
        )
    return None
