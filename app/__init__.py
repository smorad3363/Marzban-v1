import logging
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import ALLOWED_ORIGINS, DOCS, XRAY_SUBSCRIPTION_PATH

__version__ = "1.0.8"

app = FastAPI(
    title="Network Control API",
    description="Private network user, routing, and node management API",
    version=__version__,
    docs_url="/docs" if DOCS else None,
    redoc_url="/redoc" if DOCS else None,
)

scheduler = BackgroundScheduler(
    {"apscheduler.job_defaults.max_instances": 20}, timezone="UTC"
)
logger = logging.getLogger("uvicorn.error")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        body = dict(detail)
        body.setdefault("request_id", getattr(request.state, "request_id", None))
    else:
        body = {"detail": detail, "request_id": getattr(request.state, "request_id", None)}
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(body), headers=getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    logger.exception("Database integrity error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": {
                "error_code": "database_integrity_error",
                "message": "The requested change conflicts with existing data.",
                "message_fa": "این تغییر با داده‌های موجود تداخل دارد.",
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": {
                "error_code": "internal_server_error",
                "message": "An unexpected error occurred.",
                "message_fa": "خطای غیرمنتظره‌ای رخ داد.",
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    from app.jobs import start_jobs

    start_jobs()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": __version__}
