from fastapi import APIRouter
from app.api.v1 import auth,links
router=APIRouter()
router.include_router(auth.router)
router.include_router(links.router, prefix="/links", tags=["Links"])