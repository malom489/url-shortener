from fastapi import FastAPI

from app.api.v1.api import router as v1_router
from app.core.config import settings

from app.db.session import engine, Base
from app.models.users import User


app = FastAPI(
    title="url-shortener",
    version="1.0.0",
    description="A PRODUCTION GRADE MULTI-TENANT URL SHORTENER",
)

app.include_router(v1_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok", "message": "service is alive"}