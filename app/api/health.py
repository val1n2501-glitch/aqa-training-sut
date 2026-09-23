from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_session

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(request: Request, session: Annotated[Session, Depends(get_session)]):
    session.execute(text("SELECT 1"))
    return {"status": "ok", "test_mode": request.app.state.settings.test_mode}
