from fastapi import APIRouter,Depends
from app.crud_borrowing import (
    crud_create_borrowing,
    crud_return_book,
    crud_read_all_borrowing,
    crud_read_borrowing,
    crud_delete_register,
    crud_read_borrowed_books,
)

from app.schema import CreateBorrowing, ResponseBorrowing
from app.tokens import require_admin
from app.database import get_db
router=APIRouter(
    prefix="/borrowing",
    tags=["borrowing"]
)

@router.post("/")
async def borrow_book(borrow:CreateBorrowing,current_borrowing=Depends(require_admin),db=Depends(get_db)):
    return crud_create_borrowing(borrow,db)
@router.put("/")
async def returned_book(isbn:str,user_id:int,current_borrowing=Depends(require_admin),db=Depends(get_db)):
    return crud_return_book(isbn,user_id,db)
@router.get('/borrow',response_model=list[ResponseBorrowing])
async def read_all_borrowing(db=Depends(get_db)):
    return crud_read_all_borrowing(db)

@router.get("/{id}",response_model=ResponseBorrowing)
async def read_borrowing(id:int,db=Depends(get_db)):
    return crud_read_borrowing(id,db)


@router.delete("/{id}")
async def deleted_register(id:int,db=Depends(get_db)):
    return crud_delete_register(id,db)

@router.get("/",response_model=list[ResponseBorrowing])
async def read_borrowed_books(db=Depends(get_db)):
    return crud_read_borrowed_books(db)