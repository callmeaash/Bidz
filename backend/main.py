from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from models import User, Item, Bid, Comment, Wishlist, Report
from database import init_db, SessionDep
from sqlmodel import select
from dotenv import load_dotenv
import os
from datetime import timedelta, timezone
from auth import create_access_token, get_current_user
from schemas import Token, RegisterUser
from utils import get_password_hash, verify_password, USERNAME_REGEX, PASSWORD_REGEX
import re
from sqlalchemy.exc import IntegrityError

load_dotenv()

app = FastAPI()

init_db()

CurrentUserDep = Annotated[User, Depends(get_current_user)]


@app.get("/")
def index():
    return {"success": "This is index route"}


@app.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
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
    username = form_data.username.strip()
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
    
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    try:
        new_user = User(username=username, password=get_password_hash(password))
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }




@app.get("/protected")
def check(current_user: CurrentUserDep):
    return current_user