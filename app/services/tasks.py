"""Small synchronous data layer: one session per HTTP request."""

from fastapi import HTTPException
from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Task, utc_now
from app.schemas.task import TaskCreate, TaskUpdate


def get_task(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


def list_tasks(session: Session, *, q, status, priority, sort_by, order, limit, offset):
    filters = []
    if q and q.strip():
        term = q.strip().casefold()
        filters.append(
            or_(
                func.casefold(Task.title).contains(term, autoescape=True),
                func.casefold(Task.description).contains(term, autoescape=True),
            )
        )
    if status:
        filters.append(Task.status == status)
    if priority:
        filters.append(Task.priority == priority)

    total = session.scalar(select(func.count()).select_from(Task).where(*filters))
    column = getattr(Task, sort_by)  # sort_by is a validated Literal, never raw SQL.
    if sort_by == "priority":
        column = case({"low": 0, "medium": 1, "high": 2}, value=Task.priority)
    elif sort_by == "status":
        column = case({"todo": 0, "in_progress": 1, "done": 2}, value=Task.status)
    elif sort_by == "title":
        column = func.casefold(Task.title)
    direction = column.asc() if order == "asc" else column.desc()
    # Null dates always last; equal values use id ASC for stable pagination.
    ordering = [column.is_(None), direction, Task.id.asc()]
    items = session.scalars(
        select(Task).where(*filters).order_by(*ordering).limit(limit).offset(offset)
    ).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def create_task(session: Session, data: TaskCreate) -> Task:
    now = utc_now()
    task = Task(**data.model_dump(), created_at=now, updated_at=now)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def update_task(session: Session, task_id: int, data: TaskCreate | TaskUpdate) -> Task:
    task = get_task(session, task_id)
    values = data.model_dump(exclude_unset=isinstance(data, TaskUpdate))
    for name, value in values.items():
        setattr(task, name, value)
    task.updated_at = utc_now()
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: int) -> None:
    session.delete(get_task(session, task_id))
    session.commit()


def reset_tasks(session: Session, seed: bool) -> int:
    session.execute(delete(Task))
    if seed:
        timestamp = "2026-01-01T00:00:00.000000+00:00"
        session.add_all(
            [
                Task(
                    id=1,
                    title="Изучить HTTP",
                    description="Методы и статус-коды",
                    status="todo",
                    priority="high",
                    due_date=None,
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
                Task(
                    id=2,
                    title="Написать API-тест",
                    description="Проверить создание задачи",
                    status="in_progress",
                    priority="medium",
                    due_date=None,
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
                Task(
                    id=3,
                    title="Открыть Swagger",
                    description="Изучить контракт API",
                    status="done",
                    priority="low",
                    due_date=None,
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
            ]
        )
    session.commit()
    # Normal CRUD never reuses IDs; only the fixed seed has explicit IDs.
    return 3 if seed else 0
