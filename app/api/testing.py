from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import ErrorResponse
from app.db.database import get_session
from app.schemas.task import ResetRequest
from app.services.tasks import reset_tasks

router = APIRouter(prefix="/api/test", tags=["test mode"])


@router.post("/reset", responses={422: {"model": ErrorResponse}})
def reset(data: ResetRequest, session: Annotated[Session, Depends(get_session)]):
    return {"message": "Тестовые данные сброшены", "count": reset_tasks(session, data.seed)}
