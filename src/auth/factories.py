import factory

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from models import User
from utils.utils_auth import bcrypt_context
from tests.conftest import async_session_test


class UserFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = User
        sqlalchemy_session = async_session_test()

    username = factory.Sequence(lambda n: f'TestUserFactory{n}')
    email = factory.Sequence(lambda n: f'TestUserFactoryEmail{n}@test.com')
    hashed_password = factory.Sequence(lambda n: bcrypt_context.hash(f"testpassword{n}"))
