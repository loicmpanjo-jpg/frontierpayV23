"""Custom Exceptions for FrontierPay"""
from fastapi import Request
from fastapi.responses import JSONResponse


class FrontierPayException(Exception):
    def __init__(self, message: str, status_code: int = 400, error_code: str = "FRONTIERPAY_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class MerchantAuthException(FrontierPayException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401, error_code="MERCHANT_AUTH_ERROR")


class ValidationException(FrontierPayException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR")


class PSPError(FrontierPayException):
    def __init__(self, message: str = "PSP operation failed", psp: str = "unknown"):
        super().__init__(message, status_code=502, error_code=f"PSP_ERROR_{psp.upper()}")


class RoutingError(FrontierPayException):
    def __init__(self, message: str = "No routing available"):
        super().__init__(message, status_code=400, error_code="ROUTING_ERROR")


class CircuitBreakerOpen(FrontierPayException):
    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message, status_code=503, error_code="CIRCUIT_BREAKER_OPEN")


async def frontierpay_exception_handler(request: Request, exc: FrontierPayException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "status_code": exc.status_code,
        },
    )
