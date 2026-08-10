from creator.app.dtos.profile_dto import ProfileQuery
from creator.app.use_cases.profile_interactor import ProfileInteractor


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


async def test_자기소개는_실기능_정보를_반환하고_기록을_남긴다():
    record = _StubRecord()
    result = await ProfileInteractor(record=record).introduce_myself(
        ProfileQuery(id=3, name="크리에이터 (creator)")
    )
    assert result.id == 3
    assert result.name == "크리에이터 (creator)"
    assert result.introduction
    assert record.records[0][0] == "introduce_myself"
