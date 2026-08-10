from admin.app.dtos.steward_dto import StewardQuery
from admin.app.use_cases.steward_interactor import StewardInteractor


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


async def test_자기소개는_실기능_정보를_반환하고_기록을_남긴다():
    record = _StubRecord()
    result = await StewardInteractor(record=record).introduce_myself(
        StewardQuery(id=5, name="운영 (admin)")
    )
    assert result.id == 5
    assert result.introduction
    assert record.records[0][0] == "introduce_myself"
