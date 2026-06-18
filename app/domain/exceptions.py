class AppError(Exception):
    """Base application error."""


class ItemAlreadyExistsError(AppError):
    pass


class ItemNotFoundError(AppError):
    pass


class IdempotencyConflictError(AppError):
    pass


class AuthenticationError(AppError):
    pass


class IdempotencyInProgressError(AppError):
    pass


class RateLimitExceededError(AppError):
    pass
