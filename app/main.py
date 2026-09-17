from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.api import router as v1_router
from app.api.v1.redirect import router as redirect_router
from app.core.config import settings
from app.db.session import engine, Base
from app.models.user import User
from app.models.link import Link
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="url-shortener",
    version="1.0.0",
    description="A PRODUCTION GRADE MULTI-TENANT URL SHORTENER",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix=settings.API_V1_STR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
async def health():
    return {"status": "ok", "message": "service is alive"}


app.include_router(redirect_router)