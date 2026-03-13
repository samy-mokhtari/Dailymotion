class ServiceError(Exception):
    """Base class for proxy service-layer buisness errors."""

class VideoNotFoundError(ServiceError):
    """Raised when a requested video does not exist."""
