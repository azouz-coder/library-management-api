from typing import Optional,List
from fastapi import APIRouter,Depends,File,UploadFile,Query,HTTPException
from app.schema import CreateBook,ResponseBook,BookPaginatedRespons,UpdateBook
from app.crud_book import (
    crud_create_book,
    crud_read_book,
    crud_search_books,
    crud_update_book,
    crud_delete_book,
)
from app.database import get_connection , get_db
from app.tokens import require_admin
from sqlalchemy.orm import Session
from app.models import Book
import uuid
import os 

router=APIRouter(
    prefix="/books",
    tags=['books']
)
@router.post("/")
async def created_book(book:CreateBook, db = Depends(get_db),crruent_book=Depends(require_admin)):
    return crud_create_book(book,db)

@router.get("/{isbn}",response_model=ResponseBook)
async def read_book(isbn:str,db = Depends(get_db)):
    return crud_read_book(isbn,db)
@router.get("/",response_model=BookPaginatedRespons)
async def search_book(db=Depends(get_db),search: str = None ,author:str = None,  authors: Optional[List[str]]=Query(None), limit: int = Query(10,ge=1,le=100) , offset: int = Query(0,ge=0)):
    return crud_search_books(db,search,author,authors,limit,offset)

@router.put("/{isbn}")
async def update_book(isbn:str,book:UpdateBook,db = Depends(get_db),crruent_book=Depends(require_admin)):
    return crud_update_book(isbn,book,db)

@router.delete("/{isbn}")
async def delete_book(isbn:str,db=Depends(get_db),crruent_book=Depends(require_admin)):
    return crud_delete_book(isbn,db)
@router.post("/{isbn}/uploads")
async def upload_book_image(db:Session,isbn:str,file:UploadFile=File(...)):
    try:
        if file.content_type not in ["image/png","image/jpeg"]:
            raise HTTPException(
                status_code=415,
                detail="Invalid content type"
            )
        content_bytes=await file.read(8)
        JPEG_SIGNATURE=b"\xff\xd8\xff"
        PNG_SIGNATURE=b"\x89PNG\r\n\x1a\n"
        if file.content_type=="image/png" and not content_bytes.startswith(PNG_SIGNATURE):
            raise HTTPException(
                status_code=415,
                detail="Invalid image file"
            )
        if file.content_type=="image/jpeg" and not content_bytes.startswith(JPEG_SIGNATURE):
            raise HTTPException(
                status_code=415,
                detail="Invalid image file"
            )
        await file.seek(0)
        content=await file.read()
        if len(content) > (5*1024)*1024:
            raise HTTPException(
                status_code=413,
                detail="This file is bigger than allow size,Please Enter a file smaller than 5MB"
            )
        row=db.get(Book,isbn)
        if not row:
            raise HTTPException(
                status_code=404,
            detail="Book not found"
            )
        
        if file.content_type=="image/jpeg":
            extension=".jpg"
        else:
            extension=".png"
        path=os.path.join("uploads",f"{uuid.uuid4()}{extension}")
        with open(path , "wb") as f:
            f.write(content)
        db_updated=False
        try:
            row.image_path=path
            db.commit()
            db_updated=True
            old_image_path=row[3]
            if old_image_path is not None:
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
        except Exception :
            if not db_updated:
                if os.path.exists(path):
                    os.remove(path)
                raise HTTPException(
                        status_code=500,
                    detail="It happened a wrong to saved the file in database"
                )
        return {
            "message":"the file saved successfully"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise