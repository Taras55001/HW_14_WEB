from datetime import date
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy import String, ForeignKey, func, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=True)
    surname: Mapped[str] = mapped_column(String(150), index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(default=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[date] = mapped_column('crated_at', DateTime, default=func.now(), nullable=True)


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=True)
    surname: Mapped[str] = mapped_column(String(150), index=True, nullable=True)
    birthday: Mapped[date] = mapped_column(Date, index=True, nullable=True)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    phone: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(150), index=True, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user = relationship(User, backref="contacts")
