from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, status_code: int, message: str, details: dict | None = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.details = details


class LinkNotFoundError(AppException):
    def __init__(self, message: str = "Link not found", details: dict | None = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message, details=details)


class ShortCodeCollisionError(AppException):
    def __init__(self, message: str = "Short code collision", details: dict | None = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, message=message, details=details)


class UserAlreadyExistsError(AppException):
    def __init__(self, message: str = "User already exists", details: dict | None = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message, details=details)


class InvalidCredentialsError(AppException):
    def __init__(self, message: str = "Invalid credentials", details: dict | None = None):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message, details=details)

