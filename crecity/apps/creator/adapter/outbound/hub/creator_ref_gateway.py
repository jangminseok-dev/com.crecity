from __future__ import annotations

from core.database import session_scope
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from hub.app.dtos.creator_ref_dto import CreatorRef
from hub.app.ports.output.creator_ref_port import CreatorRefPort


class CreatorRefGateway(CreatorRefPort):
    """허브 CreatorRefPort 계약의 creator 구현 — main.py가 조립한다."""

    async def get_creator_by_slug(self, slug: str) -> CreatorRef | None:
        async with session_scope() as session:
            profile = await CreatorProfilePgRepository(session).find_by_slug(slug)
        if profile is None or profile.user_id is None:
            return None
        return CreatorRef(creator_user_id=profile.user_id, slug=profile.slug, name=profile.name)
