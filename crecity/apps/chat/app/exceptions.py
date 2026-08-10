class ConversationNotFoundError(Exception):
    """대화방 없음 — 라우터에서 404로 변환."""


class NotBrandAccountError(Exception):
    """브랜드 계정이 아닌 대화 시작 시도 — 라우터에서 403으로 변환."""


class CreatorNotFoundError(Exception):
    """문의 대상 크리에이터 없음 — 라우터에서 404로 변환."""


class NotConversationCreatorError(Exception):
    """대화의 크리에이터가 아닌 사용자의 오퍼 제안 — 라우터에서 403으로 변환."""
