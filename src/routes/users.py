from fastapi import APIRouter, HTTPException, Depends, status, Security, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials
from fastapi_limiter.depends import RateLimiter
import cloudinary
import cloudinary.uploader

from src.database.db import get_db
from src.routes.auth import security
from src.conf.config import settings
from src.schemas import UserResponse, UserUpdateModel, UserDeleteResponse, UserUpdateResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository import users as repository_users
from src.services.auth import auth_service

router = APIRouter(prefix="/users", tags=["users"])


@router.patch('/avatar', response_model=UserResponse)
async def update_avatar_user(file: UploadFile = File(), credentials: HTTPAuthorizationCredentials = Security(security),
                             db: AsyncSession = Depends(get_db)):
    """
    Updates a user's avatar.

    :param file: The file to uploading.
    :type file: UploadFile
    :param credentials: user token
    :type credentials: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :returns: The user instance
    :rtype: User
    """
    token = credentials.credentials
    current_user = await auth_service.authorised_user(token, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'NotesApp/{current_user.name}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.name}') \
        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user, src_url, db)
    return user


@router.put("/", response_model=UserUpdateResponse,
            description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_user(body: UserUpdateModel, credentials: HTTPAuthorizationCredentials = Security(security),
                      db: AsyncSession = Depends(get_db)):
    """
    Update user by setting the 'updated' flag to True.

    :param body: The data to update user
    :type body: UserUpdateModel
    :param credentials: user token
    :type credentials: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :returns: The user instance
    :rtype: User
    """
    token = credentials.credentials
    autorised_user = await auth_service.authorised_user(token, db)
    if not autorised_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    result = await repository_users.update_user(body, db, autorised_user)
    return result


@router.delete("/", response_model=UserDeleteResponse,
               description='No more than 10 requests per minute',
               dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def delete_user(credentials: HTTPAuthorizationCredentials = Security(security),
                      db: AsyncSession = Depends(get_db)):
    """
    Deletes a user from the database.

    :param credentials: user token
    :type credentials: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :returns: The user instance
    :rtype: User
    """
    token = credentials.credentials
    autorised_user = await auth_service.authorised_user(token, db)
    if not autorised_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    user = await repository_users.remove_user(autorised_user, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND",
        )
    return user
