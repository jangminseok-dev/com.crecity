from pydantic import BaseModel


class AppraiserResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str
