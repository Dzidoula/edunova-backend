from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Le pseudo ne peut pas être vide.")
        return value


class UserOut(BaseModel):
    id: str
    username: str

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    token: str
    user: UserOut
