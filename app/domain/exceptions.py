class AppError(Exception):
    """Base application error."""


class ItemAlreadyExistsError(AppError):
    pass


class ItemNotFoundError(AppError):
    pass


class IdempotencyConflictError(AppError):
    pass
