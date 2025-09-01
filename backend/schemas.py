from pydantic import BaseModel
from typing import Optional
from dataclasses import dataclass
from fastapi import Form, UploadFile, File
from datetime import datetime
from typing import List


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


class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class CommentRead(BaseModel):
    id: int
    comment: str
    created_at: datetime
    user: UserRead

    class Config:
        from_attributes = True


class BidRead(BaseModel):
    id: int
    bid: float
    user: UserRead

    class Config:
        from_attributes = True


class ItemRead(BaseModel):
    id: int
    owner_id: int
    title: str
    description: str
    image: str
    category: str
    starting_bid: float
    current_bid: Optional[float] = None
    created_at: datetime
    end_at: datetime
    comments: List[CommentRead] = []
    bids: List[BidRead] = []

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    comment: str


class BidCreate(BaseModel):
    bid: float


class UserBidRead(BaseModel):
    bid: float
    created_at: datetime

    class Config:
        from_attributes = True


class ItemBidInfo(BaseModel):
    id: int
    title: str
    image: str
    category: str
    current_bid: float
    user_last_bid: UserBidRead

    class Config:
        from_attributes = True