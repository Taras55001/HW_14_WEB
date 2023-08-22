from fastapi import APIRouter, HTTPException, Depends, Path, Query, status, BackgroundTasks, Security, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer

from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.schemas import UserModel, TokenModel, RequestEmail, UserResponseSignupModel

from sqlalchemy.ext.asyncio import AsyncSession

from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponseSignupModel, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request,
                 db: AsyncSession = Depends(get_db)):
    """
    Signs up a new user.

    :param body: UserModel instance containing user information.
    :type body: UserModel
    :param background_tasks: FastAPI BackgroundTasks for asynchronous tasks.
    :type background_tasks: BackgroundTasks
    :param request: FastAPI Request instance containing request information.
    :type request: Request
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :return: The created User instance.
    :rtype: UserResponseSignupModel
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exist")
    body.password = auth_service.password_manager.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user, request.base_url)
    return new_user


@router.post("/login", response_model=TokenModel, status_code=status.HTTP_200_OK)
async def login_user(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Logs in a user and returns access and refresh tokens.

    :param body: OAuth2PasswordRequestForm instance containing login information.
    :type body: OAuth2PasswordRequestForm
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :return: TokenModel instance containing access and refresh tokens.
    :rtype: TokenModel
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.password_manager.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    access_token = await auth_service.create_access_token(user)
    refresh_token = await auth_service.create_refresh_token(user)
    await repository_users.update_token(user, refresh_token, db)
    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security),
                        db: AsyncSession = Depends(get_db)):
    """
    Refreshes an access token using a refresh token.

    :param credentials: HTTPAuthorizationCredentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :return: TokenModel instance containing the new access and refresh tokens.
    :rtype: TokenModel
    """
    token = credentials.credentials
    user = await auth_service.authorised_user(token, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    access_token = await auth_service.create_access_token(user)
    refresh_token = await auth_service.create_refresh_token(user)
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms a user's email using a verification token.

    :param token: The verification token.
    :type token: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :return: A confirmation message.
    :rtype: dict
    """
    email = auth_service.jwt_manager.decode_email_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email',
             description='No more than 10 requests per 10 minutes',
             dependencies=[Depends(RateLimiter(times=10, seconds=600))])
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    Requests email confirmation for a user.

    :param body: RequestEmail instance containing the user's email.
    :type body: RequestEmail
    :param background_tasks: FastAPI BackgroundTasks for asynchronous tasks.
    :type background_tasks: BackgroundTasks
    :param request: FastAPI Request instance containing request information.
    :type request: Request
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :return: A confirmation or information message.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user, request.base_url)
    return {"message": "Check your email for confirmation."}
