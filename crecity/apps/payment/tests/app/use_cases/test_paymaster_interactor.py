from payment.app.dtos.paymaster_dto import PaymasterQuery
from payment.app.use_cases.paymaster_interactor import PaymasterInteractor


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


async def test_자기소개는_실기능_정보를_반환하고_기록을_남긴다():
    record = _StubRecord()
    result = await PaymasterInteractor(record=record).introduce_myself(
        PaymasterQuery(id=6, name="결제 (payment)")
    )
    assert result.id == 6
    assert result.introduction
    assert record.records[0][0] == "introduce_myself"
