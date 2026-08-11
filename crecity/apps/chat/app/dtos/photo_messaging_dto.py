from dataclasses import dataclass


@dataclass(frozen=True)
class SendPhotoCommand:

    conversation_id: int
    sender_user_id: int
    content: bytes
    content_type: str
