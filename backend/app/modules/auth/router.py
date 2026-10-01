from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models import User
from app.modules.auth.service import (
    authenticate_user,
    build_auth_response,
    demo_login_user,
    register_user,
)
from app.schemas.auth import (
    AuthResponse,
    DemoLoginRequest,
    LoginRequest,
    RegisterRequest,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
    return build_auth_response(user)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    profile_id = None
    if current_user.producer_profile:
        profile_id = current_user.producer_profile.id
    elif current_user.buyer_profile:
        profile_id = current_user.buyer_profile.id

    return UserOut(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        display_name=current_user.display_name,
        is_demo=current_user.is_demo,
        profile_id=profile_id,
    )


@router.post("/demo-login", response_model=AuthResponse)
def demo_login(req: DemoLoginRequest, db: Session = Depends(get_db)):
    user = demo_login_user(db, req.persona)
    return build_auth_response(user)


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, req)
    return build_auth_response(user)
