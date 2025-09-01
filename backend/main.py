from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, List
from models import User, Item, Bid, Comment, Watchlist, Report
from database import init_db, SessionDep, engine
from sqlmodel import select, Session, update
from sqlalchemy import desc, func
from dotenv import load_dotenv
import os
from datetime import timedelta, timezone, datetime
from auth import create_access_token, get_current_user, get_current_admin_user
from schemas import Token, RegisterUser, ItemForm, ItemRead, CommentCreate, CommentRead, BidRead, BidCreate, ItemBidInfo, UserBidRead
from utils import get_password_hash, verify_password, USERNAME_REGEX, PASSWORD_REGEX, NUMBER_REGEX, AUCTION_CATEGORIES
import re
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi_utils.tasks import repeat_every
from fastapi.staticfiles import StaticFiles
import time
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


app = FastAPI()

init_db()

# Allow your frontend origin
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # can also use ["*"] for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentAdminDep = Annotated[User, Depends(get_current_admin_user)]

# Image configurations
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024


# Default item image path
DEFAULT_ITEM_IMAGE = '/static/uploads/item.jpg'


# Function that runs every 60 seconds to mark the is_active status to True if end date is crossed
@app.on_event('startup')
@repeat_every(seconds=60)
def mark_ended_auctions():
    """
    Marks the is_active status of a product to true when the active time period of the auction ends
    """
    with Session(engine) as session:
        stmt = (
            update(Item)
            .where(Item.end_at <= datetime.now(timezone.utc))
            .values(is_active=False)
        )
        session.exec(stmt)
        session.commit()


@app.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    """
    Login into the auction app
    """
    username = form_data.username
    password = form_data.password

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and Password are required"
        )
    
    query = select(User).where(User.username == username)
    user = session.exec(query).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password"
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password"
        )
    access_token_expires = timedelta(minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')))
    access_token = create_access_token(
        data={'sub': str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type='bearer')


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(form_data: RegisterUser, session: SessionDep):
    """
    Register a new user
    """

    username = form_data.username.strip()
    number = form_data.number.strip()
    password = form_data.password.strip()
    confirm_password = form_data.confirm_password.strip()

    if not re.match(USERNAME_REGEX, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must start with a letter, 3-20 chars, letters/numbers/_/. only"
        )

    if not re.match(PASSWORD_REGEX, password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 chars, including a number"
        )
    
    if not re.match(NUMBER_REGEX, number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Phone number"
        )
    
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    try:
        new_user = User(username=username, number=number, password=get_password_hash(password))
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register the user {e}"
        )
    
    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


@app.post("/items", status_code=status.HTTP_201_CREATED)
async def add_item(item_data: Annotated[ItemForm, Depends()], session: SessionDep, current_user: CurrentUserDep):
    """
    Add new item in the auction
    """

    # Validate the Items data received from the user
    if len(item_data.title) < 3 or len(item_data.title) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title must be 3-50 characters"
        )
    
    if len(item_data.description) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be at least 10 characters"
        )
    
    if item_data.starting_bid <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Starting bid must be greater than 0"
        )
    
    if item_data.days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction duration must be at least 1 day"
        )
    
    if item_data.category not in AUCTION_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item category"
        )
    
    # If user provides the item image, validate the image
    file_path = DEFAULT_ITEM_IMAGE
    if item_data.image:
        if item_data.image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image type. Allowed: {",".join(ALLOWED_IMAGE_TYPES)}"
            )
        contents = await item_data.image.read()

        if len(contents) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image size must be less than {MAX_IMAGE_SIZE // (1024 * 1024)} MB"
            )

        # Save the product image in the server
        file_path = f"static/uploads/{current_user.id}_{int(time.time())}.jpg"
        with open(file_path, 'wb') as buffer:
            buffer.write(contents)

    new_item = Item(
        owner_id=current_user.id,
        title=item_data.title.title().strip(),
        description=item_data.description.capitalize().strip(),
        category=item_data.category,
        image=file_path,
        starting_bid=item_data.starting_bid,
        end_at=datetime.now(timezone.utc) + timedelta(days=item_data.days)
    )

    try:
        session.add(new_item)
        session.commit()
        session.refresh(new_item)
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create the item {e}"
        )

    return {"success": "Item added successfully"}


@app.get("/", response_model=List[Item])
def list_items(session: SessionDep, search: str | None = None):
    """
    Returns the all the active items available for bidding.
    Also allows to filter items by searching
    """
    query = select(Item).where(Item.is_active)
    if search:
        query = query.where(
            (Item.title.ilike(f"%{search}%")) | (Item.description.ilike(f"%{search}%"))
        )
    items = session.exec(query).all()
    return items


@app.get("/items/{item_id}", response_model=ItemRead)
def get_item(item_id: int, session: SessionDep):
    """
    Returns a item details for given item id
    """
    item = session.exec(select(Item).where(Item.id == item_id)).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item doesnot exist"
        )
    return item


@app.post("/item/{item_id}/comment", response_model=CommentRead)
def add_comment(item_id: int, comment_data: CommentCreate, session: SessionDep, current_user: CurrentUserDep):
    """
    Add a new comment to the item
    """

    if not comment_data.comment.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="comment cannot be all whitespaces"
        )

    try:
        new_comment = Comment(
            user_id=current_user.id,
            item_id=item_id,
            comment=comment_data.comment.strip()
        )
        session.add(new_comment)
        session.commit()
        session.refresh(new_comment)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add the comment"
        )
    return new_comment


@app.post("/item/{item_id}/bid", response_model=BidRead)
def add_bid(item_id: int, bid_data: BidCreate, session: SessionDep, current_user: CurrentUserDep):
    """
    Add a bid to the item
    """

    item = session.exec(select(Item).where(Item.id == item_id)).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Check if the user is bidding in his own item
    if item.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot bid on your own item"
        )

    if item.current_bid is None:
        if bid_data.bid < item.starting_bid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bid amount cannot be less than starting bid"
            )
    else:
        if bid_data.bid < item.current_bid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bid amount cannot be less than current bid"
            )

    try:
        item.current_bid = bid_data.bid
        session.add(item)
        new_bid = Bid(
            user_id=current_user.id,
            item_id=item_id,
            bid=bid_data.bid
        )
        session.add(new_bid)
        session.commit()
        session.refresh(new_bid)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add the bid"
        )

    return new_bid


@app.get("/my-bids", response_model=List[ItemBidInfo])
def get_my_bids(session: SessionDep, current_user: CurrentUserDep):
    """
    List items the user has bid on with their last bid
    """

    # Subquery: latest bid timestamp per item for this user
    subq = (
        select(
            Bid.item_id,
            func.max(Bid.created_at).label("last_created_at")
        )
        .where(Bid.user_id == current_user.id)
        .group_by(Bid.item_id)
        .subquery()
    )

    # Main query: join Item + last Bid
    query = (
        select(Item, Bid)
        .join(Bid, Bid.item_id == Item.id)
        .join(
            subq,
            (subq.c.item_id == Bid.item_id) &
            (subq.c.last_created_at == Bid.created_at)
        )
        .where(Bid.user_id == current_user.id)
        .order_by(subq.c.last_created_at.desc())
    )

    results = session.exec(query).all()

    return [
        ItemBidInfo(
            id=item.id,
            title=item.title,
            image=item.image,
            category=item.category,
            current_bid=item.current_bid,
            user_last_bid=UserBidRead(bid=bid.bid, created_at=bid.created_at)
        )
        for item, bid in results
    ]


@app.get("/my-watchlists")
def get_watchlists(session: SessionDep, current_user: CurrentUserDep):

    return current_user.watchlists


@app.get("/profile")
def get_profile(current_user: CurrentUserDep):
    ...

@app.get("/categories")
def categories():
    """
    Get all the categories available
    """
    return AUCTION_CATEGORIES


@app.get("/protected")
def check(current_user: CurrentUserDep):
    return {"Success": "You are user"}


@app.get("/admins")
def admins(current_user: CurrentAdminDep):
    return {"Success": "You are admin"}
