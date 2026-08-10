from campaign.app.dtos.herald_dto import HeraldQuery
from campaign.app.use_cases.herald_interactor import HeraldInteractor


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


async def test_자기소개는_실기능_정보를_반환하고_기록을_남긴다():
    record = _StubRecord()
    result = await HeraldInteractor(record=record).introduce_myself(
        HeraldQuery(id=8, name="캠페인 (campaign)")
    )
    assert result.id == 8
    assert result.introduction
    assert record.records[0][0] == "introduce_myself"
