from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import String,Integer,Boolean
class Base(DeclarativeBase):
    pass

class Book(Base):
    __tablename__="books"
    isbn : Mapped[str] = mapped_column(String,primary_key=True)
    title : Mapped[str] = mapped_column(String,nullable=False)
    author : Mapped[str] = mapped_column(String,nullable=False)
    image_path : Mapped[str | None] = mapped_column(String,nullable=True)
class User(Base):
    __tablename__="users"
    id : Mapped[int] = mapped_column(Integer,primary_key=True)
    name : Mapped[str] = mapped_column(String,nullable=False)
    email : Mapped[str] = mapped_column(String,nullable=False)
    password : Mapped[str] = mapped_column(String,nullable=False)
    role : Mapped[str] = mapped_column(String,nullable=False)
    image_profile : Mapped[str|None] = mapped_column(String,nullable=True)
    is_verified : Mapped[bool] = mapped_column(Boolean,default=False,nullable=False)