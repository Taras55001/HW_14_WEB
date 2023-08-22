import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import (get_contacts, get_contact, create_contact, remove_contact, update_contact,
                                     search_contact, upcoming_birthdays)
from src.schemas import ContactResponse


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(id=1, email='user@example.com', name='user', password='password', confirmed=True)
        self.contact = Contact(id=1, name='test', email='contact@example.com', user_id=self.user.id, user=self.user)

    async def test_get_contacts(self):
        limit = 10
        ofset = 0
        expected_response = [Contact(), Contact(), Contact()]
        mock_response = MagicMock()
        mock_response.scalars.return_value.all.return_value = expected_response
        self.session.execute.return_value = mock_response
        result = await get_contacts(limit, ofset, self.session, self.user)
        self.assertEqual(result, expected_response)

    async def test_get_contact(self):
        expected_response = self.contact
        mock_response = MagicMock()
        mock_response.scalar_one_or_none.return_value = expected_response
        self.session.execute.return_value = mock_response
        result = await get_contact(self.contact.id, self.session, self.user)
        self.assertEqual(result, expected_response)

    async def test_create_contact(self):
        body = ContactResponse(id=1, name="test name", surname="test surname", email="test@email.com",
                               phone="1234567890", birthdate=datetime.now().date())
        result = await create_contact(body, self.session, self.user)
        self.assertEqual(result.user, self.user)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.email, body.email)

    async def test_update_contact(self):
        body = ContactResponse(id=1, name="test name", surname="test surname", email="test@email.com",
                               phone="1234567890", birthdate=datetime.now().date())
        expected_response = Contact()
        mock_response = MagicMock()
        mock_response.scalar_one_or_none.return_value = expected_response
        self.session.execute.return_value = mock_response
        result = await update_contact(body.id, body, self.session, self.user)
        self.assertEqual(result.user, self.user)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.email, body.email)

    async def test_remove_contact(self):
        expected_response = self.contact
        mock_response = MagicMock()
        mock_response.scalar_one_or_none.return_value = expected_response
        self.session.execute.return_value = mock_response
        result = await remove_contact(self.contact.id, self.session, self.user)
        self.assertEqual(result, self.contact)

    async def test_search_contact(self):
        expected_response = self.contact
        mock_response = MagicMock()
        mock_response.scalars.return_value.first.return_value = expected_response
        self.session.execute.return_value = mock_response
        result = await search_contact(self.user, self.session, contact_name="", surname="tes", email="")
        self.assertEqual(result, expected_response)

    async def test_upcoming_birthdays(self):
        current_date = datetime.now().date()
        future_birthday = current_date + timedelta(days=7)
        expected_response = [Contact(birthday=current_date), Contact(birthday=future_birthday)]
        mock_response = MagicMock()
        mock_response.scalars.return_value.all.return_value = expected_response
        self.session.execute.return_value = mock_response
        result = await upcoming_birthdays(self.user, self.session)
        self.assertLessEqual(result[0].birthday, future_birthday)
        self.assertLessEqual(result[1].birthday, future_birthday)
        self.assertGreaterEqual(result[0].birthday, current_date)
        self.assertGreaterEqual(result[1].birthday, current_date)




if __name__ == '__main__':
    unittest.main()
