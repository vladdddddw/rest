from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    id: str
    username: str
    is_active: bool

    model_config = {"from_attributes": True}
