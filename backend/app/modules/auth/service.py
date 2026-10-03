from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import BuyerProfile, ProducerProfile, User
from app.db.seed import CANONICAL_PERSONAS
from app.schemas.auth import RegisterRequest, UserOut

settings = get_settings()


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise AppException(
            status_code=401,
            code="UNAUTHENTICATED",
            message="Invalid email or password.",
        )
    return user


def demo_login_user(db: Session, persona: str) -> User:
    if not settings.DEMO_MODE:
        raise AppException(
            status_code=404,
            code="DEMO_DISABLED",
            message="Demo mode is disabled on this server.",
        )

    if settings.APP_ENV == "production" and persona == "operator":
        raise AppException(
            status_code=403,
            code="FORBIDDEN",
            message="Operator persona login via demo-login is disabled in production environments. Use credentials via /auth/login.",
        )

    email = CANONICAL_PERSONAS.get(persona)
    if not email:
        raise AppException(
            status_code=422,
            code="VALIDATION_ERROR",
            message=f"Unknown persona '{persona}'. Must be one of: {list(CANONICAL_PERSONAS.keys())}.",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise AppException(
            status_code=404,
            code="NOT_FOUND",
            message=f"User for persona '{persona}' not found in demo database.",
        )
    return user


def register_user(db: Session, req: RegisterRequest) -> User:
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise AppException(
            status_code=409,
            code="CONFLICT",
            message="A user with this email address already exists.",
        )

    # Validate coordinates inside India bounding box
    prof_data = req.profile
    lat = prof_data.get("lat")
    lng = prof_data.get("lng")
    if (
        lat is None
        or lng is None
        or not (6.0 <= float(lat) <= 38.0 and 68.0 <= float(lng) <= 98.0)
    ):
        raise AppException(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Location coordinates must fall within India bounding box (lat 6-38, lng 68-98).",
            details=[{"field": "profile.lat/lng", "issue": "Outside India bounds"}],
        )

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        role=req.role,
        display_name=req.display_name,
        is_demo=False,
    )
    db.add(user)
    db.flush()

    if req.role == "PRODUCER":
        producer_profile = ProducerProfile(
            user_id=user.id,
            producer_type=prof_data.get("producer_type", "FARMER"),
            org_name=prof_data.get("org_name", req.display_name),
            state=prof_data.get("state", "Delhi"),
            district=prof_data.get("district", "Delhi"),
            locality=prof_data.get("locality"),
            lat=float(lat),
            lng=float(lng),
            member_farmers=prof_data.get("member_farmers"),
            is_demo=False,
        )
        db.add(producer_profile)
    elif req.role == "BUYER":
        hub_id = prof_data.get("hub_id", 1)
        buyer_profile = BuyerProfile(
            user_id=user.id,
            buyer_type=prof_data.get("buyer_type", "RETAILER"),
            org_name=prof_data.get("org_name", req.display_name),
            hub_id=int(hub_id),
            city=prof_data.get("city", "Delhi"),
            state=prof_data.get("state", "Delhi"),
            lat=float(lat),
            lng=float(lng),
            is_demo=False,
        )
        db.add(buyer_profile)

    db.commit()
    db.refresh(user)
    return user


def build_auth_response(user: User) -> dict:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    profile_id = None
    if user.producer_profile:
        profile_id = user.producer_profile.id
    elif user.buyer_profile:
        profile_id = user.buyer_profile.id

    user_out = UserOut(
        id=user.id,
        email=user.email,
        role=user.role,
        display_name=user.display_name,
        is_demo=user.is_demo,
        profile_id=profile_id,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_out,
    }
