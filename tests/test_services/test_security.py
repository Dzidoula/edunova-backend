import pytest
import jwt

from app.core.security import create_access_token, decode_access_token


def test_round_trip_token():
    token = create_access_token(user_id="abc-123", username="koffi")
    payload = decode_access_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["username"] == "koffi"


def test_invalid_token_raises():
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("not-a-real-token")
