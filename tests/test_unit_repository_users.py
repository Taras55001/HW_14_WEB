import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.users import (
    get_user_by_email, confirmed_email, create_user, update_token, update_user, update_avatar, remove_user
)
from src.schemas import UserModel, UserUpdateModel


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(id=1, email='user@example.com', name='user', password='password', confirmed=True)



    async def test_get_user_by_email(self):
        expected_response = self.user
        mock_response = MagicMock()
        mock_response.scalar_one_or_none.return_value = expected_response
        self.session.execute.return_value = mock_response
        result = await get_user_by_email(self.user.email, self.session)
        self.assertEqual(result, expected_response)

    async def test_confirmed_email(self):
        expected_response = self.user
        mock_response = MagicMock()
        mock_response.scalar_one_or_none.return_value = expected_response
        self.session.execute.return_value = mock_response
        await confirmed_email(self.user.email, self.session)
        result = await get_user_by_email(self.user.email, self.session)
        self.assertTrue(result.confirmed)

    async def test_create_user(self):
        body = UserModel(name=self.user.name, email=self.user.email, password=self.user.password)
        mock_db = self.session
        result = await create_user(body, mock_db)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)
        self.assertFalse(result.confirmed)

    async def test_update_token(self):
        token = "token"
        self.user.refresh_token = token
        await update_token(self.user, token, self.session)
        expected_response = self.user
        mock_response = MagicMock()
        mock_response.scalar_one_or_none.return_value = expected_response
        self.session.execute.return_value = mock_response
        result = await get_user_by_email(self.user.email, self.session)
        self.assertEqual(result.refresh_token, token)

    async def test_update_user(self):
        body = UserUpdateModel(name="testupdate", surname="test", email="testemail@mail.com", phone="1234567890")
        result = await update_user(body, self.session, self.user)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.phone, body.phone)

    async def test_update_avatar(self):
        url = 'http://test.com'
        result = await update_avatar(self.user, url, self.session)
        self.assertEqual(result.avatar, url)

    async def test_remove_user(self):
        result = await remove_user(self.user, self.session)
        self.assertEqual(result, self.user)


if __name__ == '__main__':
    unittest.main()
