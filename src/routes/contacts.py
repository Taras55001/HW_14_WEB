from typing import List

from fastapi import APIRouter, HTTPException, Depends, Path, Query, status, Security
from fastapi.security import HTTPAuthorizationCredentials
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.routes.auth import security
from src.schemas import ContactResponse, ContactModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository import contacts as response_contacts
from src.services.auth import auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=List[ContactResponse], status_code=status.HTTP_200_OK,
             description='No more than 10 requests per minute',
             dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_contacts(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0, le=200),
                       credentials: HTTPAuthorizationCredentials = Security(security),
                       db: AsyncSession = Depends(get_db)):
    """
    Gets the contact information for a given user.

    :param limit: The maximum number of contacts to retrieve.
    :type limit: int
    :param offset: The number of contacts to skip before retrieving.
    :type offset: int
    :param credentials: user token
    :type credentials: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :return: A list of Contact instances.
    :rtype: list
    """
    token = credentials.credentials
    user = await auth_service.authorised_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    contacts = await response_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse,
             description='No more than 10 requests per minute',
             dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_contact(contact_id: int = Path(ge=1), credentials: HTTPAuthorizationCredentials = Security(security),
                      db: AsyncSession = Depends(get_db)):
    """
    Retrieves a contact from database session.

    :param contact_id: An id of the contact
    :type contact_id: int
    :param credentials: user token
    :type credentials: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :return: The Contact instance
    :rtype: Contact
    """
    token = credentials.credentials
    user = await auth_service.authorised_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    contact = await response_contacts.get_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND",
        )
    return contact


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             description='No more than 5 requests per minute',
             dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_contact(body: ContactModel,
                         credentials: HTTPAuthorizationCredentials = Security(security),
                         db: AsyncSession = Depends(get_db)):
    """
    Creates a new contact for a user.

    :param body: ContactResponse instance containing contact information.
    :type body: ContactResponse
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param credentials: user token
    :type credentials: str
    :return: The created Contact instance
    :rtype: Contact
    """
    token = credentials.credentials
    user = await auth_service.authorised_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    contact = await response_contacts.create_contact(body, db, user)
    if not contact:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact already exist")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             description='No more than 10 requests per minute',
             dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_contact(body: ContactModel, contact_id: int = Path(ge=1),
                         credentials: HTTPAuthorizationCredentials = Security(security),
                         db: AsyncSession = Depends(get_db)):
    """
    Updates an existing contact's information.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: ContactModel instance containing updated contact information.
    :type body: ContactModel
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param credentials: user token
    :type credentials: str
    :return: The updated Contact instance
    :rtype: Contact
    """
    token = credentials.credentials
    user = await auth_service.authorised_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    contact = await response_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND",
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT,
             description='No more than 5 requests per minute',
             dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def remove_contact(contact_id: int = Path(ge=1),
                         credentials: HTTPAuthorizationCredentials = Security(security),
                         db: AsyncSession = Depends(get_db)):
    """
    Removes a contact from the database.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param credentials: user token
    :type credentials: str
    :return: The Contact instance
    :rtype: Contact
    """

    token = credentials.credentials
    user = await auth_service.authorised_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    contact = await response_contacts.remove_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND",
        )
    return contact


@router.get("/search/{user_id}", response_model=ContactResponse, status_code=status.HTTP_200_OK,
             description='No more than 15 requests per minute',
             dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def search_contact(credentials: HTTPAuthorizationCredentials = Security(security),
                         contact_name: str = Query(None, min_length=2),
                         surname: str = Query(None, min_length=2),
                         email: str = Query(None),
                         db: AsyncSession = Depends(get_db)
                         ):
    """
    Searches for a contact based on the provided criteria.

    :param credentials: user token
    :type credentials: str
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param contact_name: The name of the contact to search for.
    :type contact_name: str
    :param surname: The surname of the contact to search for.
    :type surname: str
    :param email: The email of the contact to search for.
    :type email: str
    :return: The first matching Contact instance
    :rtype: Contact
    """
    token = credentials.credentials
    user = await auth_service.authorised_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    contact = await response_contacts.search_contact(user, db, contact_name, surname, email)
    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="NOT FOUND",
        )
    return contact


@router.get("/birthdays/{user_id}", response_model=List[ContactResponse],
             description='No more than 10 requests per minute',
             dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def upcoming_birthdays(credentials: HTTPAuthorizationCredentials = Security(security),
                             db: AsyncSession = Depends(get_db)):
    """
    Retrieves contacts with upcoming birthdays within the next 7 days.

    :param credentials: user token
    :type credentials: str
    :param db: The database session.
    :type db: AsyncSession
    :return: A list of Contact instances with upcoming birthdays.
    :rtype: list
    """
    token = credentials.credentials
    user = await auth_service.authorised_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    contacts = await response_contacts.upcoming_birthdays(user, db)
    if not contacts:
        raise HTTPException(
            status_code=404,
            detail="No upcoming birthdays found for the user.",
        )
    return contacts
