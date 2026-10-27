from app.database import get_connection
from sqlalchemy.orm import Session
from sqlalchemy import select,func,or_,and_
from fastapi import HTTPException
from typing import Optional,List
from models import Book

def crud_create_book(book,db:Session):
    try:
        verirfy_book= db.get(Book,book.isbn)
        if verirfy_book is not None:
            raise HTTPException(
                status_code=409,
                detail="Book already to creat"
            )
        new_book = Book(isbn=book.isbn,title=book.title,author=book.author)
        db.add(new_book)
        db.commit()

        return {
            "message":"Book added seccussfully"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

def crud_read_book(isbn:str, db:Session):
    try:
        book =db.get(Book,isbn)
        if book is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )
        return {
            "isbn":book.isbn,
            "title":book.title,
            "author":book.author
        }
    except HTTPException:
        raise
    
def crud_search_books(db:Session,search: str = None ,author: str =None, authors: Optional[List[str]]=None, limit: int = 10 , offset : int = 0):

        conditions=[]
        if search:
            search_term=f"%{search}%"
            conditions.append(or_(Book.isbn.ilike(search_term),Book.title.ilike(search_term),Book.author.ilike(search_term)))
        if author:
            conditions.append(Book.author==author)
        if authors:
            conditions.append(Book.author.in_(authors))
            
        if conditions:
            where_clause= and_(*conditions)
        stmt = select(func.count()).select_from(Book)
        if conditions:
            stmt = stmt.where(where_clause)
        total = db.execute(stmt).scalar()
        if conditions:
            stmt = select(Book).where(where_clause).order_by(Book.title).limit(limit).offset(offset)
            books= db.execute(stmt).scalars().all()
        else:
            stmt = select(Book).order_by(Book.title).limit(limit).offset(offset)
            books= db.execute(stmt).scalars().all()
            
        return {
            "total":total,
            "items":[{
                "isbn":book.isbn,
                "title":book.title,
                "author":book.author
            }for book in books]
        }
        
def crud_update_book(isbn:str,book,db:Session):
    conn=None
    try:
        book_update=db.get(Book,isbn)
        if book_update is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )
        if book.title is None and book.author is None:
            raise HTTPException(
                status_code=409,
                detail="There is no data"
            )
        if book.title is not None:
            book_update.title=book.title
        if book.author is not None:
            book_update.author=book.author
        db.commit()
        
        return {
            "message":"Book updated seccussfully"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

def crud_delete_book(isbn:str,db:Session):
    try:
        book_delete=db.get(Book,isbn)
        if book_delete is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )
        db.delete(book_delete)
        db.commit()
        return{
            "message":"Book deleted seccussfully"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise