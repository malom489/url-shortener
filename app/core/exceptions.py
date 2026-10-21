from fastapi import status

class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class LinkNotFoundError(AppException):
    pass

class ShortCodeCollisionError(AppException):
    pass

class UserAlreadyExistsError(AppException):
    pass

class InvalidCredentialsError(AppException):
    pass

class LinkCreationError(AppException):
    pass