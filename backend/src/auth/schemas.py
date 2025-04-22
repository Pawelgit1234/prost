import re

from pydantic import BaseModel, Field, EmailStr, field_validator

class UserRegisterSchema(BaseModel):
    first_name: str = Field(max_length=32)
    last_name: str = Field(max_length=32)
    description: str | None = Field(default=None, max_length=100) # optional
    username: str = Field(min_length=3, max_length=16)
    email: EmailStr = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=16)

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r'[A-Z]', value):
            raise ValueError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', value):
            raise ValueError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one digit.')
        if not re.search(r'[^A-Za-z0-9]', value):
            raise ValueError('Password must contain at least one special character.')
        return value
    
class TokenSchema(BaseModel):
    access_token: str
    token_type: str

class TokenDataSchema(BaseModel):
    username: str