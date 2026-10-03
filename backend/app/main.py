import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database import Base, engine
from app.routers import admin, audit, auth, family, patients, reports, system, visits, webhooks, worklist

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cara")

settings.validate()

# Schema bootstrap. SQLite demo databases are created on first start; for a
# long-lived Postgres database run migrations before deploying instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Cara tracks whether mothers and newborns complete their postnatal follow-up visits "
        "after discharge, sends non-clinical WhatsApp/SMS reminders and gives coordinators a "
        "ranked worklist. All endpoints except auth, health and webhooks need a Bearer token."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s %s %.1fms rid=%s", request.method, request.url.path, response.status_code, elapsed_ms, request_id
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    # Turn pydantic's error list into one sentence the UI can show as-is.
    messages, errors = [], []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", [])]
        field = ".".join(p for p in loc if p not in ("body", "query", "path"))
        msg = err.get("msg", "Invalid value").removeprefix("Value error, ")
        messages.append(f"{field.replace('_', ' ')}: {msg}" if field else msg)
        errors.append({"loc": loc, "msg": msg, "type": err.get("type")})
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages), "errors": errors})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side. Please try again."})


for module in (system, auth, patients, worklist, visits, family, reports, audit, admin, webhooks):
    app.include_router(module.router)


@app.get("/", include_in_schema=False)
def root():
    return {"service": settings.PROJECT_NAME, "version": settings.VERSION, "docs": "/api/docs"}
