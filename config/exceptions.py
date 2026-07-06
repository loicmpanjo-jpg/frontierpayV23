"""Hierarchical exception classes for the entire platform."""


class AFMException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail


class AuthenticationError(AFMException):
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"
    detail = "Authentication failed"


class AuthorizationError(AFMException):
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"
    detail = "Insufficient permissions"


class ValidationError(AFMException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    detail = "Invalid input data"


class NotFoundError(AFMException):
    status_code = 404
    error_code = "NOT_FOUND"
    detail = "Resource not found"


class ConflictError(AFMException):
    status_code = 409
    error_code = "CONFLICT"
    detail = "Resource conflict"


class RateLimitError(AFMException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    detail = "Rate limit exceeded"


class MarketClosedError(AFMException):
    status_code = 400
    error_code = "MARKET_CLOSED"
    detail = "Market is currently closed"


class BrokerUnavailableError(AFMException):
    status_code = 503
    error_code = "BROKER_UNAVAILABLE"
    detail = "No broker available for this market"


class PaymentError(AFMException):
    status_code = 400
    error_code = "PAYMENT_FAILED"
    detail = "Payment processing failed"


class InsufficientFundsError(AFMException):
    status_code = 400
    error_code = "INSUFFICIENT_FUNDS"
    detail = "Insufficient funds for this operation"


class CurrencyNotSupportedError(AFMException):
    status_code = 400
    error_code = "CURRENCY_NOT_SUPPORTED"
    detail = "Currency not supported"


class SelfFollowError(AFMException):
    status_code = 400
    error_code = "SELF_FOLLOW"
    detail = "Cannot copy-trade yourself"


class InvalidAllocationError(AFMException):
    status_code = 400
    error_code = "INVALID_ALLOCATION"
    detail = "Invalid allocation percentage"


class APIKeyExpiredError(AFMException):
    status_code = 401
    error_code = "API_KEY_EXPIRED"
    detail = "API key has expired"
