from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session
from app.schemas.core import DashboardOut
from app.services.dashboard import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(db_session)) -> DashboardOut:
    return DashboardService(db).get()
