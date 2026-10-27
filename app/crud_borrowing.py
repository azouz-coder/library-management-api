from app.database import get_connection
from fastapi import HTTPException
from datetime import datetime,timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Book,User,Borrowing
def crud_create_borrowing(borrow,db:Session):
    try:
        now=datetime.now(timezone.utc).isoformat()
        book = db.get(Book,borrow.isbn)
        if book is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )
        stmt = select(Borrowing).where(Borrowing.isbn==borrow.isbn,Borrowing.returned_at.is_(None))
        borrowing = db.execute(stmt).scalar_one_or_none()
        if borrowing:
            raise HTTPException(
                status_code=409,
                detail="Book not available"
            )
        user = db.get(User,borrow.user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        new_borrowing = Borrowing(user_id=borrow.user_id,isbn=borrow.isbn,borrowed_at=now)
        db.add(new_borrowing)
        db.commit()
        return{
            "message":"Book borrowed successfully"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

def crud_return_book(isbn:str,user_id:int,db:Session):
    try:
        now=datetime.now(timezone.utc).isoformat()
        book = db.get(Book,isbn)
        if book is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )
        user = db.get(User,user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        stmt = select(Borrowing).where(Borrowing.isbn==isbn,Borrowing.user_id==user_id,Borrowing.returned_at.is_(None))
        returning = db.execute(stmt).scalar_one_or_none()
        if returning is None:
            raise HTTPException(
                status_code=404,
                detail="Book not available"
            )
        returning.returned_at=now
        db.commit()
        return{
            "message":"Book returned successfully"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

def crud_read_borrowing(id:int,db:Session):
        stmt = (select(User.name,Book.title,Borrowing.borrowed_at,Borrowing.returned_at).join(User,User.id==Borrowing.user_id).join(Book,Book.isbn==Borrowing.isbn)).where(Borrowing.id==id)
        result = db.execute(stmt).first()
        if result is None:
            raise HTTPException(
                status_code=404,
                detail="This register is not found"
            )
        return {
            "name":result._mapping["name"],
            "title":result._mapping["title"],
            "borrowed_at":result._mapping["borrowed_at"],
            "returned_at":result._mapping["returned_at"]
        }
def crud_read_all_borrowing(db:Session):
        stmt = (select(User.name,Book.title,Borrowing.borrowed_at,Borrowing.returned_at).join(User,Borrowing.user_id==User.id).join(Book,Borrowing.isbn==Book.isbn))
        result = db.execute(stmt).mappings().all()
        if not result:
            raise HTTPException(
                status_code=404,
                detail="This register is not found"
            )
        return [dict(row) for row in result]   

def crud_delete_register(id:int,db:Session):
    try:
        stmt = select(Borrowing).where(Borrowing.id==id)
        borrow_data = db.execute(stmt).scalar_one_or_none()
        if borrow_data is None:
            raise HTTPException(
                status_code=404,
                detail="Borrowing record not found"
            )
        if borrow_data.returned_at is None:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete a borrowing record befor the is returned"
            )
        db.delete(borrow_data)
        db.commit()
        return {
            "massage":"Borrowing record deleted successfully"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
def crud_read_borrowed_books(db:Session):
        stmt = (select(User.name,Book.title,Borrowing.borrowed_at,Borrowing.returned_at).join(User,Borrowing.user_id==User.id).join(Book,Borrowing.isbn==Book.isbn)).where(Borrowing.returned_at.is_(None))
        result = db.execute(stmt).mappings().all()
        if not result:
            raise HTTPException(
                status_code=404,
                detail="No books borrowed"
            )
        return [dict(row) for row in result]