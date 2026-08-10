from dataclasses import dataclass


@dataclass(frozen=True)
class StewardQuery:

    id: int
    name: str


@dataclass(frozen=True)
class StewardResponse:

    id: int
    name: str
    introduction: str
