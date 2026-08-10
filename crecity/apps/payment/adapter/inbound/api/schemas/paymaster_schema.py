from pydantic import BaseModel


class PaymasterResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str
