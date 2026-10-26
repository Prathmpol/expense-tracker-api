from datetime import timedelta

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_hash_password_returns_hashed_value():
    password = "MySecurePassword123"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("CorrectPassword123")

    assert not verify_password("WrongPassword123", hashed)


def test_create_and_decode_access_token():
    token = create_access_token({"sub": "user123"})

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "user123"
    assert "exp" in payload


def test_decode_invalid_token_returns_none():
    payload = decode_access_token("this.is.not-a-valid-token")

    assert payload is None


def test_decode_expired_token_returns_none():
    token = create_access_token(
        {"sub": "user123"},
        expires_delta=timedelta(seconds=-1),
    )

    payload = decode_access_token(token)

    assert payload is None