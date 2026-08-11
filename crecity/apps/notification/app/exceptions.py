class NotificationNotFoundError(Exception):
    """id에 해당하는 알림 없음(또는 본인 알림이 아님) — 라우터에서 404로 변환."""
