import base64
import binascii

from app.services.errors import (
    InvalidAuthorizationHeaderError,
    MissingAuthorizationHeaderError,
)


def decode_moderator_name(authorization_header: str | None) -> str:
    if authorization_header is None:
        raise MissingAuthorizationHeaderError

    raw_value = authorization_header.strip()
    if not raw_value:
        raise InvalidAuthorizationHeaderError

    try:
        decoded_bytes = base64.b64decode(raw_value, validate=True)
        moderator_name = decoded_bytes.decode("utf-8").strip()
    except (binascii.Error, UnicodeDecodeError) as error:
        raise InvalidAuthorizationHeaderError from error

    if not moderator_name:
        raise InvalidAuthorizationHeaderError

    return moderator_name
