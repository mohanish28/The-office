import pytest

from app.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "user-123", "is_owner": True})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["is_owner"] is True


def test_decode_invalid_token():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("not.a.real.token")
