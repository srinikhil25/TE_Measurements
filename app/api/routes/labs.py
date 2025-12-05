from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lab import Lab as LabModel
from app.schemas.lab import Lab as LabSchema

router = APIRouter()


@router.get("/", response_model=List[LabSchema])
def list_labs(db: Session = Depends(get_db)):
    """Return list of all labs (for lab selection screen)."""
    labs = db.query(LabModel).order_by(LabModel.lab_name.asc()).all()
    return labs


