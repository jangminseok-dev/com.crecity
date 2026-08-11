from fastapi import APIRouter, Depends, HTTPException, Response

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from notification.adapter.inbound.api.schemas.notification_listing_schema import (
    NotificationItemSchema,
    NotificationsResponseSchema,
)
from notification.app.exceptions import NotificationNotFoundError
from notification.app.ports.input.notification_listing_use_case import (
    NotificationListingUseCase,
)
from notification.dependencies.notification_listing_provider import (
    get_notification_listing_use_case,
)

notification_listing_router = APIRouter(prefix="/notification", tags=["notification"])


@notification_listing_router.get("/notifications", response_model=NotificationsResponseSchema)
async def list_my_notifications(
    user: VerifiedUser = Depends(get_current_user),
    use_case: NotificationListingUseCase = Depends(get_notification_listing_use_case),
) -> NotificationsResponseSchema:
    result = await use_case.list_mine(user.id)
    return NotificationsResponseSchema(
        unread_count=result.unread_count,
        items=[
            NotificationItemSchema(
                id=item.id,
                event_type=item.event_type,
                body=item.body,
                link=item.link,
                is_read=item.is_read,
                created_at=item.created_at,
            )
            for item in result.items
        ],
    )


@notification_listing_router.post("/notifications/read-all", status_code=204)
async def mark_all_read(
    user: VerifiedUser = Depends(get_current_user),
    use_case: NotificationListingUseCase = Depends(get_notification_listing_use_case),
) -> Response:
    await use_case.mark_all_read(user.id)
    return Response(status_code=204)


@notification_listing_router.post("/notifications/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: NotificationListingUseCase = Depends(get_notification_listing_use_case),
) -> Response:
    try:
        await use_case.mark_read(user.id, notification_id)
    except NotificationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return Response(status_code=204)
