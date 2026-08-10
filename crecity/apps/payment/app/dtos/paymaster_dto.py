from dataclasses import dataclass


@dataclass(frozen=True)
class PaymasterQuery:

    id: int
    name: str


@dataclass(frozen=True)
class PaymasterResponse:

    id: int
    name: str
    introduction: str
