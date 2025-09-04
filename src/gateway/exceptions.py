"""Custom exceptions for the gateway service."""


class GatewayError(Exception):
    """Base exception for all gateway service errors."""
    pass


class HTTPError(GatewayError):
    """Raised when HTTP operations fail."""

    def __init__(self, status_code=None, message=None, *args, **kwargs):
        """
        Initialize with status code and message.

        Args:
            status_code: HTTP status code if available
            message: Error message
        """
        self.status_code = status_code
        super().__init__(
            message or f"HTTP error occurred, status code: {status_code}", *args, **kwargs)


class RepositoryError(GatewayError):
    """Raised when repository operations fail."""
    pass


class FactPodServiceError(GatewayError):
    """Raised when Fact Pod service operations fail."""
    pass
