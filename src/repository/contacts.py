from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from src.database.models import Contact, User
from src.schemas import ContactResponse


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    """
    Retrieves a list of contacts for a specified user.

    :param limit: The maximum number of contacts to retrieve.
    :type limit: int
    :param offset: The number of contacts to skip before retrieving.
    :type offset: int
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param user: The User instance representing the user.
    :type user: User
    :return: A list of Contact instances.
    :rtype: list
    """

    sq = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(sq)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user: User):
    """
    Retrieves a contact from database session.

    :param contact_id: An id of the contact
    :type contact_id: int
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param user: The User instance representing the user.
    :type user: User
    :return: The Contact instance or None
    :rtype: Contact or None
    """

    sq = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(sq)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactResponse, db: AsyncSession, user: User):
    """
    Creates a new contact for a user.

    :param body: ContactResponse instance containing contact information.
    :type body: ContactResponse
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param user: The User instance representing the user.
    :type user: User
    :return: The created Contact instance or None if an IntegrityError occurs.
    :rtype: Contact or None
    """

    try:
        contact = Contact(name=body.name, surname=body.surname, birthday=body.birthday, phone=body.phone,
                          email=body.email,
                          user=user)
        if body.description:
            contact.description = body.description
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        return contact
    except IntegrityError as e:
        await db.rollback()
        return None


async def update_contact(contact_id: int, body: ContactResponse, db: AsyncSession, user: User):
    """
    Updates an existing contact's information.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: ContactResponse instance containing updated contact information.
    :type body: ContactResponse
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param user: The User instance representing the user.
    :type user: User
    :return: The updated Contact instance or None if the contact is not found.
    :rtype: Contact or None
    """

    sq = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(sq)
    contact = result.scalar_one_or_none()
    if contact:
        contact.name = body.name
        contact.surname = body.surname
        contact.phone = body.phone
        contact.email = body.email
        contact.user = user
        contact.description = body.description
        await db.commit()
        await db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, db: AsyncSession, user: User):
    """
    Removes a contact from the database.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param user: The User instance representing the user.
    :type user: User
    :return: The Contact instance
    :rtype: Contact
    """

    sq = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(sq)
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def search_contact(user: User,
                         db: AsyncSession,
                         contact_name: str,
                         surname: str,
                         email: str):
    """
    Searches for a contact based on the provided criteria.

    :param user: The User instance representing the user.
    :type user: User
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :param contact_name: The name of the contact to search for.
    :type contact_name: str
    :param surname: The surname of the contact to search for.
    :type surname: str
    :param email: The email of the contact to search for.
    :type email: str
    :return: The first matching Contact instance or None if no match is found.
    :rtype: Contact or None
    """

    sq = select(Contact).filter_by(user=user)
    if contact_name:
        sq = sq.filter(or_(Contact.name.ilike(f'%{contact_name}%')))
    elif surname:
        sq = sq.filter(or_(Contact.surname.ilike(f'%{surname}%')))
    elif email:
        sq = sq.filter(or_(Contact.email.ilike(f'%{email}%')))

    result = await db.execute(sq)
    contact_found = result.scalars().first()
    return contact_found


async def upcoming_birthdays(user: User, db: AsyncSession):
    """
    Retrieves contacts with upcoming birthdays within the next 7 days.

    :param user: The User instance representing the user.
    :type user: User
    :param db: The database session.
    :type db: AsyncSession
    :return: A list of Contact instances with upcoming birthdays.
    :rtype: list
    """

    current_date = datetime.now().date()
    future_birthday = current_date + timedelta(days=7)
    sq = select(Contact).filter_by(user=user)
    result = await db.execute(sq)
    list_bd_contacts = result.scalars().all()
    happy_contacts = []
    for data in list_bd_contacts:
        ccy = data.birthday.replace(year=current_date.year)
        cfy = data.birthday.replace(year=future_birthday.year)
        if ccy >= current_date and cfy <= future_birthday:
            happy_contacts.append(data)
    return happy_contacts
