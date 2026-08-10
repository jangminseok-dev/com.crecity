from notification.app.dtos.bellman_dto import BellmanQuery
from notification.app.use_cases.bellman_interactor import BellmanInteractor


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


async def test_자기소개는_실기능_정보를_반환하고_기록을_남긴다():
    record = _StubRecord()
    result = await BellmanInteractor(record=record).introduce_myself(
        BellmanQuery(id=10, name="알림 (notification)")
    )
    assert result.id == 10
    assert result.introduction
    assert record.records[0][0] == "introduce_myself"
