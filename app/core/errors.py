from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException


class ErrorDetail(BaseModel):
    loc: list[str | int]
    message: str
    type: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail]


class ErrorResponse(BaseModel):
    error: ErrorBody


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Некорректные входные данные",
                    "details": [
                        {"loc": list(e["loc"]), "message": e["msg"], "type": e["type"]}
                        for e in exc.errors()
                    ],
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={
                "error": {
                    "code": "not_found" if exc.status_code == 404 else "http_error",
                    "message": str(exc.detail),
                    "details": [],
                }
            },
        )
