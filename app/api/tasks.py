from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.core.errors import ErrorResponse
from app.db.database import get_session
from app.schemas.task import (
    Order,
    Priority,
    SortBy,
    Status,
    TaskCreate,
    TaskList,
    TaskResponse,
    TaskUpdate,
)
from app.services import tasks

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
Database = Annotated[Session, Depends(get_session)]
# SQLite stores integers in a signed 64-bit range. Reject overflow before SQL.
MAX_SQLITE_INTEGER = 2**63 - 1
TaskId = Annotated[int, Path(gt=0, le=MAX_SQLITE_INTEGER)]


@router.get("", response_model=TaskList)
def list_tasks(
    session: Database,
    q: Annotated[str | None, Query(max_length=200)] = None,
    status: Status | None = None,
    priority: Priority | None = None,
    sort_by: SortBy = "id",
    order: Order = "asc",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=MAX_SQLITE_INTEGER)] = 0,
):
    return tasks.list_tasks(
        session,
        q=q,
        status=status,
        priority=priority,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(data: TaskCreate, session: Database):
    return tasks.create_task(session, data)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: TaskId, session: Database):
    return tasks.get_task(session, task_id)


@router.put("/{task_id}", response_model=TaskResponse)
def replace_task(task_id: TaskId, data: TaskCreate, session: Database):
    """Replace user fields; omitted optional fields return to their defaults."""
    return tasks.update_task(session, task_id, data)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: TaskId, data: TaskUpdate, session: Database):
    return tasks.update_task(session, task_id, data)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: TaskId, session: Database):
    tasks.delete_task(session, task_id)
    return Response(status_code=204)
