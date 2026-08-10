from dataclasses import dataclass


@dataclass(frozen=True)
class HeraldQuery:

    id: int
    name: str


@dataclass(frozen=True)
class HeraldResponse:

    id: int
    name: str
    introduction: str
