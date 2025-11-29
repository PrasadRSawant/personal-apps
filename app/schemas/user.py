from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str = Field(..., max_length=72)

class UserInDB(UserBase):
    id: str
    is_active: bool
    auth_method: str
