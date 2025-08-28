from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, Enum, func
from datetime import datetime, timezone
from typing import List


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(sa_column=Column(String, unique=True, nullable=False))
    password: str
    avatar: str = Field(
        default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png",
        sa_column=Column(String, server_default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png", nullable=False)
    )
    is_admin: bool = Field(
        default=False,
        sa_column=Column(Boolean, server_default="false", nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    items: List["Item"] = Relationship(back_populates="owner")
    wishlists: List["Wishlist"] = Relationship(back_populates="user")

    def __str__(self):
        return f"{self.username}"


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete='CASCADE'), nullable=False))
    title: str
    description: str
    image: str = Field(
        default="https://png.pngtree.com/png-vector/20221125/ourmid/pngtree-no-image-available-icon-flatvector-illustration-picture-coming-creative-vector-png-image_40968940.jpg",
        sa_column=Column(String, server_default="https://png.pngtree.com/png-vector/20221125/ourmid/pngtree-no-image-available-icon-flatvector-illustration-picture-coming-creative-vector-png-image_40968940.jpg", nullable=False)
    )
    starting_bid: float
    current_bid: float
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, server_default="true", nullable=False)
    )
    winner: int | None = Field(default=None)
    end_at: datetime
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )

    owner: User = Relationship(back_populates="items")
    bids: List["Bid"] = Relationship(back_populates="item")
    comments: List["Comment"] = Relationship(back_populates="item")

    def __str__(self):
        return f"{self.title}"


class Bid(SQLModel, table=True):
    __tablename__ = "bids"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete='CASCADE')))
    item_id: int = Field(sa_column=Column(ForeignKey("items.id", ondelete='CASCADE')))
    bid: float
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )

    item: Item = Relationship(back_populates='bids')


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete='CASCADE')))
    item_id: int = Field(sa_column=Column(ForeignKey("items.id", ondelete='CASCADE')))
    comment: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )

    item: Item = Relationship(back_populates="comments")


class Wishlist(SQLModel, table=True):
    __tablename__ = "watchlists"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete='CASCADE')))
    item_id: int = Field(sa_column=Column(ForeignKey("items.id", ondelete='CASCADE')))
    user: User = Relationship(back_populates="wishlists")


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: int = Field(default=None, primary_key=True)
    reporter_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete='CASCADE')))
    target_id: int = Field(sa_column=Column(ForeignKey("items.id", ondelete='CASCADE')))
    status: str = Field(
        sa_column=Column(Enum('pending', 'resolved', name='report_status_enum'), server_default='pending', nullable=False)
    )
