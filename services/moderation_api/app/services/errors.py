class ServiceError(Exception):
    """Base class for service-layer business errors."""


class VideoAlreadyExistsError(ServiceError):
    """Raised when trying to add a video that already exists in the queue."""


class VideoNotFoundError(ServiceError):
    """Raised when a requested video does not exist."""


class MissingAuthorizationHeaderError(ServiceError):
    """Raised when the Authorization header is missing."""


class InvalidAuthorizationHeaderError(ServiceError):
    """Raised when the Authorization header is invalid or cannot be decoded."""


class NoVideoAvailableError(ServiceError):
    """Raised when no pending video is available for moderation."""
