from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    # AC-SEC-01
    plain = "secretPassword123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrongPassword", hashed) is False


def test_token_creation_and_decoding():
    # AC-AUTH-01
    data = {"sub": "42", "role": "PRODUCER"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "42"
    assert decoded["role"] == "PRODUCER"
    assert "exp" in decoded


def test_expired_or_tampered_token():
    # AC-SEC-02
    data = {"sub": "42", "role": "PRODUCER"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-10))
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token(token)

    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("this.is.notavalidtoken")
