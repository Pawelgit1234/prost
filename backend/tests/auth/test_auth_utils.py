from datetime import timedelta

import pytest
from fastapi import HTTPException
from src.auth.utils import verify_password, get_password_hash, create_jwt_token, \
    decode_jwt_token

def test_password_hashing_and_verification():
    password = 'secret'
    password_hash = get_password_hash(password)
    
    assert password != password_hash
    assert verify_password(password, password_hash)
    assert not verify_password('wrong secret', password_hash)

def test_create_and_decode_jwt_token():
    data = {'sub': 'username'}
    token = create_jwt_token(data, timedelta(minutes=10))
    decoded_data = decode_jwt_token(token)
    assert data['sub'] == decoded_data.username

def test_invalid_token_raises_exception():
    with pytest.raises(HTTPException):
        decode_jwt_token('not.a.valid.token')