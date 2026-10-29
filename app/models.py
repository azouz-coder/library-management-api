from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import String,Integer,Boolean , ForeignKey
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
    email : Mapped[str] = mapped_column(String,nullable=False,unique=True)
    password : Mapped[str] = mapped_column(String,nullable=False)
    role : Mapped[str] = mapped_column(String,nullable=False)
    image_profile : Mapped[str|None] = mapped_column(String,nullable=True)
    is_verified : Mapped[bool] = mapped_column(Boolean,default=False,nullable=False)
class Borrowing(Base):
    __tablename__="borrowing"
    id : Mapped[int] = mapped_column(Integer,primary_key=True)
    isbn : Mapped[str] = mapped_column(String,ForeignKey("books.isbn",ondelete="CASCADE"),nullable=False)
    user_id : Mapped[int] = mapped_column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    borrowed_at : Mapped[str] = mapped_column(String,nullable=True)
    returned_at : Mapped[str] = mapped_column(String,nullable=True)
class EmailVerification(Base):
    __tablename__="email_verifications"
    id : Mapped[int] = mapped_column(Integer , primary_key=True)
    user_id : Mapped[int] = mapped_column(Integer,ForeignKey("users.id",ondelete="CASCADE"), nullable=False )
    token_hash : Mapped[str] = mapped_column(String,nullable=False)
    expires_at : Mapped[str] = mapped_column(String,nullable=False)
    used : Mapped[bool] = mapped_column(Boolean,default=False)
class RefreshTokens(Base):
    __tablename__="refresh_tokens"
    id : Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id : Mapped[int] = mapped_column(Integer,nullable=False)
    hash_token : Mapped[str] = mapped_column(String,nullable=False)
    create_at : Mapped[str] = mapped_column(String,nullable=False)
    expire_at : Mapped[str] = mapped_column(String,nullable=False)
    revoked : Mapped[int] = mapped_column(Integer,nullable=False)
class PasswordResets(Base):
    __tablename__="password_resets"
    id : Mapped[int] = mapped_column(Integer , primary_key=True)
    user_id : Mapped[int] = mapped_column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    token_hash : Mapped[str] = mapped_column(String,nullable=False)
    expires_at : Mapped[str] = mapped_column(String,nullable=False)
    used : Mapped[bool] = mapped_column(Boolean,default=False)
