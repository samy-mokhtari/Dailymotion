class ServiceError(Exception):
    """Base class for service-layer business errors."""


class VideoAlreadyExistsError(ServiceError):
    """Raised when trying to add a video that already exists in the queue."""


class VideoNotFoundError(ServiceError):
    """Raised when a requested video does not exist."""
