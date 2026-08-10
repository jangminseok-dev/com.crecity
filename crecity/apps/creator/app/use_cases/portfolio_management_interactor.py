from __future__ import annotations

from creator.app.dtos.portfolio_management_dto import (
    PortfolioItemResult,
    PortfolioListQuery,
    PortfolioRemovalCommand,
    PortfolioUploadCommand,
)
from creator.app.exceptions import (
    NotProfileOwnerError,
    PortfolioItemNotFoundError,
    PortfolioLimitExceededError,
    ProfileNotFoundError,
)
from creator.app.ports.input.portfolio_management_use_case import PortfolioManagementUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.app.ports.output.portfolio_file_storage import PortfolioFileStorage
from creator.app.ports.output.portfolio_item_repository import PortfolioItemRepository
from creator.domain.entities.portfolio_item_entity import PortfolioItem
from creator.domain.value_objects.image_file import ImageFile

# 프로필당 사진 상한 — 갤러리 한 화면 분량
_MAX_ITEMS_PER_PROFILE = 12


def _to_result(item: PortfolioItem) -> PortfolioItemResult:
    return PortfolioItemResult(
        id=item.id,
        profile_id=item.profile_id,
        file_name=item.file_name,
        created_at=item.created_at,
    )


class PortfolioManagementInteractor(PortfolioManagementUseCase):

    def __init__(
        self,
        profiles: CreatorProfileRepository,
        items: PortfolioItemRepository,
        storage: PortfolioFileStorage,
    ) -> None:
        self._profiles = profiles
        self._items = items
        self._storage = storage

    async def upload(self, command: PortfolioUploadCommand) -> PortfolioItemResult:
        profile = await self._profiles.find_by_user_id(command.requester_user_id)
        if profile is None:
            raise ProfileNotFoundError("프로필을 먼저 등록해야 포트폴리오를 올릴 수 있습니다.")
        if await self._items.count_by_profile_id(profile.id) >= _MAX_ITEMS_PER_PROFILE:
            raise PortfolioLimitExceededError(
                f"포트폴리오는 최대 {_MAX_ITEMS_PER_PROFILE}장까지 올릴 수 있습니다."
            )
        image = ImageFile(content=command.content, content_type=command.content_type)
        file_name = self._storage.save(image.content, image.extension)
        item = await self._items.create(profile_id=profile.id, file_name=file_name)
        return _to_result(item)

    async def remove(self, command: PortfolioRemovalCommand) -> None:
        item = await self._items.find_by_id(command.item_id)
        if item is None:
            raise PortfolioItemNotFoundError(f"포트폴리오 항목을 찾을 수 없습니다: {command.item_id}")
        profile = await self._profiles.find_by_id(item.profile_id)
        if profile is None:  # FK가 보장하므로 정상 경로에선 불가능 — 데이터 손상 신호
            raise RuntimeError(f"항목이 가리키는 프로필이 없습니다: profile_id={item.profile_id}")
        if not profile.is_owned_by(command.requester_user_id):
            raise NotProfileOwnerError("본인 프로필의 포트폴리오만 삭제할 수 있습니다.")
        if not await self._items.delete(command.item_id):
            raise PortfolioItemNotFoundError(f"포트폴리오 항목을 찾을 수 없습니다: {command.item_id}")
        # DB 삭제가 정본 — 파일 삭제는 뒤따르는 정리(실패해도 항목은 이미 사라짐)
        self._storage.delete(item.file_name)

    async def list_for_profile(self, query: PortfolioListQuery) -> list[PortfolioItemResult]:
        profile = await self._profiles.find_by_slug(query.slug)
        if profile is None:
            raise ProfileNotFoundError(f"프로필을 찾을 수 없습니다: {query.slug}")
        items = await self._items.list_by_profile_id(profile.id)
        return [_to_result(item) for item in items]
