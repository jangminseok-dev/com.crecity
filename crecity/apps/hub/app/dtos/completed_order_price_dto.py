from dataclasses import dataclass


@dataclass(frozen=True)
class PackageOrderAmount:
    """완료 주문 1건의 (패키지, 거래가) — 시세 집계(갭 #89) 재료.

    분류(카테고리·플랫폼)는 creator가 자기 데이터로 해석하므로 여기엔 싣지 않는다.
    """

    package_id: int
    amount_krw: int
