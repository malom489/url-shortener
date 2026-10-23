from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, engine
from app.db.redis import redis_client 
from app.api.v1.api import router as v1_router
from app.api.v1.redirect import router as redirect_router
from app.core.config import settings
from app.core.handlers import register_exception_handlers

import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    logger.info("Starting up... Checking dependencies.")
    
    # 1. Check Database
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection established.")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not connect to database. {e}")
        
    # 2. Check Redis
    try:
        await redis_client.ping()
        logger.info("✅ Redis connection established.")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not connect to Redis. {e}")

    yield # The app runs here
    
    logger.info("Shutting down...")
    await engine.dispose()
    await redis_client.aclose() # Use aclose() for redis.asyncio


app = FastAPI(
    title="url-shortener",
    version="1.0.0",
    description="A PRODUCTION GRADE MULTI-TENANT URL SHORTENER",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Fixed the typo here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )

@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

# --- HEALTH CHECK ---
@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "database": "unhealthy",
        "redis": "unhealthy"
    }
    
    # 1. Check Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"

    # 2. Check Redis
    try:
        await redis_client.ping()
        health_status["redis"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"

    # 3. Return 503 if anything is down
    if health_status["status"] == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )

    return health_status

# Include Routers
app.include_router(v1_router, prefix=settings.API_V1_STR)
app.include_router(redirect_router)