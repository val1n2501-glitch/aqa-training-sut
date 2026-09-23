import re
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

Status = Literal["todo", "in_progress", "done"]
Priority = Literal["low", "medium", "high"]
SortBy = Literal["id", "title", "status", "priority", "due_date", "created_at", "updated_at"]
Order = Literal["asc", "desc"]


def strip_title(value):
    return value.strip() if isinstance(value, str) else value


def check_date(value):
    if value is None or (isinstance(value, date) and not isinstance(value, datetime)):
        return value
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Expected a date in YYYY-MM-DD format")
    return value


Title = Annotated[str, Field(min_length=1, max_length=120), BeforeValidator(strip_title)]
Description = Annotated[str, Field(max_length=2000)]
DueDate = Annotated[date | None, BeforeValidator(check_date)]


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: Description = ""
    status: Status = "todo"
    priority: Priority = "medium"
    due_date: DueDate = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    description: Description | None = None
    status: Status | None = None
    priority: Priority | None = None
    due_date: DueDate = None

    @model_validator(mode="after")
    def reject_empty_and_null(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field")
        for name in self.model_fields_set - {"due_date"}:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class TaskResponse(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TaskList(BaseModel):
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    seed: bool = False
