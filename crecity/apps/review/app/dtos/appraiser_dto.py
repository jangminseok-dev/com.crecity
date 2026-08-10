from dataclasses import dataclass


@dataclass(frozen=True)
class AppraiserQuery:

    id: int
    name: str


@dataclass(frozen=True)
class AppraiserResponse:

    id: int
    name: str
    introduction: str
