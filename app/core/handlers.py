from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    AppException,
    LinkNotFoundError,
    ShortCodeCollisionError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    LinkCreationError
)

def register_exception_handlers(app: FastAPI) -> None:
    """Map domain exceptions to HTTP responses."""

    @app.exception_handler(LinkNotFoundError)
    async def link_not_found_handler(request: Request, exc: LinkNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "link_not_found", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(ShortCodeCollisionError)
    async def collision_handler(request: Request, exc: ShortCodeCollisionError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "short_code_collision", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "user_already_exists", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "invalid_credentials", "message": exc.message, "details": exc.details},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(LinkCreationError)
    async def link_creation_handler(request: Request, exc: LinkCreationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "link_creation_error", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(AppException)
    async def generic_app_handler(request: Request, exc: AppException):
        # Fallback for any AppException that doesn't have a specific handler
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "internal_error", "message": exc.message, "details": exc.details},
        )