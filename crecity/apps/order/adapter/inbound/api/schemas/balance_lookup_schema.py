from pydantic import BaseModel


class BalanceResponseSchema(BaseModel):

    user_id: int
    balance_krw: int
