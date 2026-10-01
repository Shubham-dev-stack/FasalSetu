from pydantic import BaseModel, ConfigDict, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=1)


class DemoLoginRequest(BaseModel):
    persona: str = Field(..., description="One of the canonical demo personas")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    display_name: str
    is_demo: bool
    profile_id: int | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RegisterRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(PRODUCER|BUYER)$")
    display_name: str = Field(..., min_length=2)
    profile: dict
