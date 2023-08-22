from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserUpdateModel, UserModel


async def get_user_by_email(email: str, db: AsyncSession) -> User:
    """
    Gets a user from the database by email address.

    :param email: The email address of the user to get.
    :type email: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :returns: The user from the database corresponding to the given email.
    :rtype: User
    """
    sq = select(User).filter_by(email=email)
    result = await db.execute(sq)
    user = result.scalar_one_or_none()
    return user


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Confirms a user's email by setting the 'confirmed' flag to True.

    :param email: The email address of the user to confirm.
    :type email: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()
    await db.refresh(user)


async def create_user(body: UserModel, db: AsyncSession) -> User:
    """
    Creates a user in the database.

    :param body: The user parameters
    :type body: UserModel
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :returns: The user from the database
    :rtype: User
    """
    user = User(**body.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_token(user: User, token: str | None, db: AsyncSession) -> None:
    """
    Updates an authentication token for a user.

    :param token: The authentication token to update.
    :type token: str
    :param user: The user object to update the token for.
    :type user: User
    :param db: An asynchronous database session.
    :type db: AsyncSession
    """
    user.refresh_token = token
    await db.commit()
    await db.refresh(user)


async def update_user(body: UserUpdateModel, db: AsyncSession, user: User) -> User:
    """
    Update a user's information.

    :param user: The user object to update.
    :type user: User
    :param body: The new data for the user.
    :type body: UserResponse
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :returns: The user from the database
    :rtype: User
    """
    if body.name is not None:
        user.name = body.name
    if body.surname is not None:
        user.surname = body.surname
    if body.phone is not None:
        user.phone = body.phone
    if body.email is not None:
        user.email = body.email
        await db.commit()
        await db.refresh(user)
    return user


async def update_avatar(user: User, url: str, db: AsyncSession) -> User:
    """
    Updates a user's avatar.

    :param user: The user object to update.
    :type user: User
    :param url: The URL of the avatar to set.
    :type url: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :returns: The user from the database corresponding to the given email.
    :rtype: User
    """
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def remove_user(user: User, db: AsyncSession) -> User:
    """
    Removes a user from the database.

    :param user: The user object to remove.
    :type user: User
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :returns: The user object
    :rtype: User
    """
    await db.delete(user)
    await db.commit()
    return user
