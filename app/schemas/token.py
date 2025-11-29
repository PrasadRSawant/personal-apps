# Inside app/schemas/token.py
from pydantic import BaseModel, ConfigDict

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)

class TokenData(BaseModel):
    username: str | None = None
    model_config = ConfigDict(from_attributes=True)
