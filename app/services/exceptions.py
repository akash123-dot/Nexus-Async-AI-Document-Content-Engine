
class AppBaseException(Exception):
    def __init__(self, detail: str, status_code: int):
        self.detail = detail
        self.status_code = status_code

class NotFoundException(AppBaseException):
    def __init__(self, detail: str = "Not found"):
        super().__init__(detail, status_code=404)

class BadRequestException(AppBaseException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(detail, status_code=400)

class ForbiddenException(AppBaseException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail, status_code=403)


class UserAlreadyExistsError(AppBaseException):
    def __init__(self, detail: str = "User already exists"):
        super().__init__(detail, status_code=409)

class InvalidCredentialsException(AppBaseException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail, status_code=401)

class BlueskyAccountNotConnected(AppBaseException):
    def __init__(self, detail: str = "Bluesky account not connected"):
        super().__init__(detail, status_code=400)