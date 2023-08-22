from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

from src.conf.config import settings

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


from datetime import date

from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship



class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=True)
    surname: Mapped[str] = mapped_column(String(150), index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)

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


Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
