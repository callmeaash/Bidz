from passlib.context import CryptContext
from sqlmodel import Session, update
from database import engine
from models import Item
from datetime import datetime, timezone


USERNAME_REGEX = r'^[a-zA-Z][a-zA-Z0-9_.]{2,19}$'
PASSWORD_REGEX = r'^(?=.*\d)[A-Za-z\d]{6,}$'
NUMBER_REGEX = r'^(?:97|98)\d{8}$'
AUCTION_CATEGORIES = {
    "Electronics",
    "Fashion",
    "Home & Garden",
    "Sports",
    "Books",
    "Collectibles",
    "Art",
    "Toys",
    "Jewelry",
    "Vehicles",
    "Miscellaneous"
}

pwd_context = CryptContext(schemes=['bcrypt'])


def get_password_hash(plain_password) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def mark_ended_auctions():
    with Session(engine) as session:
        stmt = (
            update(Item)
            .where(Item.end_at <= datetime.now(timezone.utc))
            .values(is_active=False)
        )
        session.exec(stmt)
        session.commit()
