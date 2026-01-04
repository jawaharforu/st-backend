from typing import Optional
from sqlmodel import SQLModel

class Token(SQLModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenPayload(SQLModel):
    sub: Optional[str] = None
