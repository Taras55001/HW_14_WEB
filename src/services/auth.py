"""
Module Name: auth.py
Description: This module provides authentication and authorization functionalities using FastAPI and JWT tokens.

Contents:
- PasswordManager: A class for managing password encryption and verification.
- JWTManager: A class for JWT token creation and decoding.
- AuthService: A class handling user authentication and authorization.

Dependencies:
- fastapi, jose, passlib, datetime, sqlalchemy, src.database.db, src.repository.users1, src.conf.config

Usage:
1. Import the necessary classes and modules:
    from src.authentication import PasswordManager, JWTManager, AuthService, oauth2_scheme

2. Initialize the required settings:
    - secret_key: Secret key used for JWT token encoding.
    - algorithm: JWT token encoding algorithm.

3. Initialize the authentication service:
    auth_service = AuthService(PasswordManager(), JWTManager(secret_key, algorithm), repository_users, redis_sessionmanager)

4. Use the authentication service for various operations:
    - authenticate_user(email: str, password: str, db: AsyncSession) -> User: Authenticate a user based on email and password.
    - authorised_user(token: str, db: AsyncSession) -> User: Validate and authorize a user using an access token.
    - create_access_token(user: User) -> str: Create an access token for a user.
    - create_refresh_token(user: User) -> str: Create a refresh token for a user.
    - create_email_token(user: User) -> str: Create an email verification token for a user.

Note: Replace 'User' with your actual user class or data structure.
"""
from typing import Dict, Any, Optional
import pickle

from fastapi import HTTPException, status, Depends
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db, redis_sessionmanager
from src.repository import users as repository_users

from src.conf.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class PasswordManager:
    """
    Class responsible for managing password encryption and verification.
    """
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)


class JWTManager:
    """
    Class responsible for JWT token creation and decoding.
    """
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, data: Dict[str, Any], scope: str, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": scope})
        encoded_token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_token

    def decode_token(self, token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    def decode_email_token(self, token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload['scope'] == 'email_token':
                email = payload['sub']
                return email
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')


class AuthService:
    """
    Class providing user authentication and authorization services.
    """
    def __init__(self, password_manager, jwt_manager, user_repository, redis):
        self.r = redis
        self.password_manager = password_manager
        self.jwt_manager = jwt_manager
        self.user_repository = user_repository

    async def authenticate_user(self, email: str, password: str, db: AsyncSession):
        user = await self.user_repository.get_user_by_email(email, db)
        if user is None or not self.password_manager.verify_password(password, user.password):
            return None
        return user

    async def authorised_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        try:
            email = self.jwt_manager.decode_token(token)
        except JWTError:
            return None
        user = self.r.redis.get(f"user:{email}")
        if user is None:
            user = await self.user_repository.get_user_by_email(email, db)
            if user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')
            self.r.redis.set(f"user:{email}", pickle.dumps(user))
            self.r.redis.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user

    async def create_access_token(self, user):
        access_token_expires = 900
        access_token_data = {"sub": user.email}
        return self.jwt_manager.create_token(access_token_data, "access_token", access_token_expires)

    async def create_refresh_token(self, user):
        refresh_token_expires = 604800
        refresh_token_data = {"sub": user.email}
        token = self.jwt_manager.create_token(refresh_token_data, "refresh_token", refresh_token_expires)
        return token

    async def create_email_token(self, user):
        refresh_token_expires = 604800
        refresh_token_data = {"sub": user.email}
        token = self.jwt_manager.create_token(refresh_token_data, "email_token", refresh_token_expires)
        return token



secret_key = settings.secret_key
algorithm = settings.algorithm

auth_service = AuthService(PasswordManager(), JWTManager(secret_key, algorithm), repository_users, redis_sessionmanager)
