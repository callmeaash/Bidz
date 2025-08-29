from pydantic import BaseModel
from typing import Optional
from dataclasses import dataclass
from fastapi import Form, UploadFile, File


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: int | None = None


class RegisterUser(BaseModel):
    username: str
    number: str
    password: str
    confirm_password: str


@dataclass
class ItemForm:
    title: str = Form(...)
    description: str = Form(...)
    category: str = Form(...)
    starting_bid: float = Form(...)
    days: int = Form(...)
    image: Optional[UploadFile] = File(None)

