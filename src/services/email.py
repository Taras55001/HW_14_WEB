from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors

from src.services.auth import auth_service
from src.database.models import User

from src.conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(user: User, host: str):
    """
    Email verify the user's email address.

    :param user: The user object for whom the email verification is being sent.
    :type user: User
    :param host: The hostname or URL where the verification link will point to.
    :type host: str
    """
    try:
        token_verification = await auth_service.create_email_token(user)
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[user.email],
            template_body={"host": host, "name": user.name, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)
