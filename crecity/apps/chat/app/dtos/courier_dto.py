from dataclasses import dataclass


@dataclass(frozen=True)
class CourierQuery:

    id: int
    name: str


@dataclass(frozen=True)
class CourierResponse:

    id: int
    name: str
    introduction: str
