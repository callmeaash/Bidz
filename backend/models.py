from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, Enum, func, Float, PrimaryKeyConstraint
from datetime import datetime, timezone
from typing import List, Optional


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(sa_column=Column(String, unique=True, nullable=False))
    password: str
    number: str
    avatar: str = Field(
        default="/static/uploads/avatar.jpg",
        sa_column=Column(String, server_default="/static/uploads/avatar.jpg", nullable=False)
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

    owned_items: List["Item"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "Item.owner_id"}
    )
    won_items: List["Item"] = Relationship(
        back_populates="winner",
        sa_relationship_kwargs={"foreign_keys": "Item.winner_id"}
    )
     
    watchlists: List["Watchlist"] = Relationship(back_populates="user")

    comments: List["Comment"] = Relationship(back_populates="user")
    bids: List["Bid"] = Relationship(back_populates="user")

    def __str__(self):
        return f"{self.username}"


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete='CASCADE'), nullable=False))
    title: str
    description: str
    image: str = Field(
        sa_column=Column(String, server_default="/static/uploads/item.jpg", nullable=False)
    )
    category: str
    starting_bid: float
    current_bid: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True)
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, server_default="true", nullable=False)
    )
    winner_id: int | None = Field(
        default=None,
        sa_column=Column(ForeignKey("users.id", ondelete='SET NULL'), nullable=True)
    )
    end_at: datetime
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )

    owner: User = Relationship(
        back_populates="owned_items",
        sa_relationship_kwargs={"foreign_keys": "Item.owner_id"}
    )
    winner: User | None = Relationship(
        back_populates="won_items",
        sa_relationship_kwargs={"foreign_keys": "Item.winner_id"}
    )
    
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
    user: User = Relationship(back_populates="bids")


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
    user: User = Relationship(back_populates="comments")


class Watchlist(SQLModel, table=True):
    __tablename__ = "wishlists"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "item_id"),
    )

    user_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete='CASCADE')))
    item_id: int = Field(sa_column=Column(ForeignKey("items.id", ondelete='CASCADE')))
    user: User = Relationship(back_populates="watchlists")


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: int = Field(default=None, primary_key=True)
    reporter_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete='CASCADE')))
    target_id: int = Field(sa_column=Column(ForeignKey("items.id", ondelete='CASCADE')))
    status: str = Field(
        sa_column=Column(Enum('pending', 'resolved', name='report_status_enum'), server_default='pending', nullable=False)
    )
