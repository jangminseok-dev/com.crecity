import pytest

from creator.app.dtos.portfolio_management_dto import (
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
from creator.app.use_cases.portfolio_management_interactor import (
    PortfolioManagementInteractor,
)
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from creator.domain.entities.portfolio_item_entity import PortfolioItem

OWNER, STRANGER = 10, 99


def _profile(id=1, user_id=OWNER):
    return CreatorProfile(
        id=id, slug="kim-beauty", name="김뷰티", tagline="t", bio="b",
        primary_category="뷰티", location="서울", status=ProfileStatus.APPROVED,
        user_id=user_id,
    )


class _StubProfileRepository:
    def __init__(self, profile):
        self.profile = profile

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile and self.profile.user_id == user_id else None

    async def find_by_id(self, profile_id):
        return self.profile if self.profile and self.profile.id == profile_id else None

    async def find_by_slug(self, slug):
        return self.profile if self.profile and self.profile.slug == slug else None


class _StubItemRepository:
    def __init__(self, items=None):
        self.items = list(items or [])
        self.deleted = []

    async def create(self, profile_id, file_name):
        item = PortfolioItem(id=len(self.items) + 1, profile_id=profile_id, file_name=file_name)
        self.items.append(item)
        return item

    async def find_by_id(self, item_id):
        return next((i for i in self.items if i.id == item_id), None)

    async def list_by_profile_id(self, profile_id):
        return [i for i in self.items if i.profile_id == profile_id]

    async def count_by_profile_id(self, profile_id):
        return len([i for i in self.items if i.profile_id == profile_id])

    async def delete(self, item_id):
        before = len(self.items)
        self.items = [i for i in self.items if i.id != item_id]
        removed = len(self.items) < before
        if removed:
            self.deleted.append(item_id)
        return removed


class _StubFileStorage:
    def __init__(self):
        self.saved = []
        self.deleted = []

    def save(self, content, extension):
        name = f"file{len(self.saved)}.{extension}"
        self.saved.append(name)
        return name

    def delete(self, file_name):
        self.deleted.append(file_name)


def _interactor(profile=None, items=None):
    profiles = _StubProfileRepository(profile if profile is not None else _profile())
    item_repo = _StubItemRepository(items)
    storage = _StubFileStorage()
    return PortfolioManagementInteractor(profiles, item_repo, storage), item_repo, storage


def _upload(user_id=OWNER, content=b"img", content_type="image/jpeg"):
    return PortfolioUploadCommand(
        requester_user_id=user_id, content=content, content_type=content_type
    )


async def test_업로드하면_파일이_저장되고_항목이_생긴다():
    interactor, item_repo, storage = _interactor()
    result = await interactor.upload(_upload())
    assert result.file_name == "file0.jpg"
    assert storage.saved == ["file0.jpg"]
    assert len(item_repo.items) == 1


async def test_프로필이_없으면_업로드할_수_없다():
    interactor, _, _ = _interactor()
    with pytest.raises(ProfileNotFoundError):
        await interactor.upload(_upload(user_id=STRANGER))


async def test_상한을_넘기면_업로드가_거부된다():
    full = [PortfolioItem(id=i + 1, profile_id=1, file_name=f"f{i}.jpg") for i in range(12)]
    interactor, _, storage = _interactor(items=full)
    with pytest.raises(PortfolioLimitExceededError):
        await interactor.upload(_upload())
    assert storage.saved == []  # 거부 시 파일을 만들지 않는다


async def test_지원하지_않는_형식은_거부된다():
    interactor, _, _ = _interactor()
    with pytest.raises(ValueError):
        await interactor.upload(_upload(content_type="image/gif"))


async def test_소유자는_삭제할_수_있고_파일도_정리된다():
    items = [PortfolioItem(id=1, profile_id=1, file_name="a.jpg")]
    interactor, item_repo, storage = _interactor(items=items)
    await interactor.remove(PortfolioRemovalCommand(item_id=1, requester_user_id=OWNER))
    assert item_repo.items == []
    assert storage.deleted == ["a.jpg"]


async def test_타인의_항목은_삭제할_수_없다():
    items = [PortfolioItem(id=1, profile_id=1, file_name="a.jpg")]
    interactor, item_repo, _ = _interactor(items=items)
    with pytest.raises(NotProfileOwnerError):
        await interactor.remove(PortfolioRemovalCommand(item_id=1, requester_user_id=STRANGER))
    assert len(item_repo.items) == 1


async def test_없는_항목_삭제는_404다():
    interactor, _, _ = _interactor()
    with pytest.raises(PortfolioItemNotFoundError):
        await interactor.remove(PortfolioRemovalCommand(item_id=77, requester_user_id=OWNER))


async def test_슬러그로_공개_목록을_조회한다():
    items = [
        PortfolioItem(id=1, profile_id=1, file_name="a.jpg"),
        PortfolioItem(id=2, profile_id=1, file_name="b.jpg"),
    ]
    interactor, _, _ = _interactor(items=items)
    results = await interactor.list_for_profile(PortfolioListQuery(slug="kim-beauty"))
    assert [r.file_name for r in results] == ["a.jpg", "b.jpg"]


async def test_없는_슬러그_목록_조회는_404다():
    interactor, _, _ = _interactor()
    with pytest.raises(ProfileNotFoundError):
        await interactor.list_for_profile(PortfolioListQuery(slug="ghost"))
