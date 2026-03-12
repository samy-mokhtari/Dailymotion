import pytest
from app.services.auth import decode_moderator_name
from app.services.errors import (
    InvalidAuthorizationHeaderError,
    MissingAuthorizationHeaderError,
)


def test_decode_moderator_name_returns_decoded_value() -> None:
    result = decode_moderator_name("am9obi5kb2U=")

    assert result == "john.doe"


def test_decode_moderator_name_strips_decoded_value() -> None:
    result = decode_moderator_name("ICBqb2huLmRvZSAg")

    assert result == "john.doe"


def test_decode_moderator_name_raises_when_header_is_missing() -> None:
    with pytest.raises(MissingAuthorizationHeaderError):
        decode_moderator_name(None)


def test_decode_moderator_name_raises_when_header_is_blank() -> None:
    with pytest.raises(InvalidAuthorizationHeaderError):
        decode_moderator_name("   ")


def test_decode_moderator_name_raises_when_header_is_not_valid_base64() -> None:
    with pytest.raises(InvalidAuthorizationHeaderError):
        decode_moderator_name("not-base64")


def test_decode_moderator_name_raises_when_decoded_value_is_blank() -> None:
    with pytest.raises(InvalidAuthorizationHeaderError):
        decode_moderator_name("ICAg")
