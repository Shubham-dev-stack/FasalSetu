from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.reference.service import get_reference_data
from app.schemas.reference import ReferenceResponse

router = APIRouter(tags=["reference"])


@router.get("/reference", response_model=ReferenceResponse)
def get_reference(db: Session = Depends(get_db)):
    return get_reference_data(db)
