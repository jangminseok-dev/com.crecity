class OrderNotFoundError(Exception):
    """리뷰 대상 주문 없음 — 라우터에서 404로 변환."""


class NotOrderBrandError(Exception):
    """주문한 브랜드가 아닌 리뷰 시도 — 라우터에서 403으로 변환."""


class OrderNotCompletedError(Exception):
    """완료되지 않은 주문의 리뷰 시도 — 라우터에서 409로 변환."""


class ReviewAlreadyExistsError(Exception):
    """이미 리뷰가 있는 주문(주문당 1개) — 라우터에서 409로 변환."""


class ReviewNotFoundError(Exception):
    """리뷰 없음 — 라우터에서 404로 변환."""


class CreatorNotFoundError(Exception):
    """리뷰 조회 대상 크리에이터 없음 — 라우터에서 404로 변환."""


class NotOrderCreatorError(Exception):
    """브랜드 리뷰(갭 #83)는 주문을 수행한 크리에이터만 쓸 수 있다 — 라우터에서 403."""
