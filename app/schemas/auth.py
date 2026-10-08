from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_valid(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Le mot de passe doit contenir au moins 6 caractères.")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Le mot de passe est trop long (72 octets maximum).")
        return value

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
