from fastapi import APIRouter,Depends,UploadFile,File,HTTPException
from sqlalchemy.orm import Session
from app.schema import CreateUser,UpdatedUser,ResponseUser,RespondeLogin,EmailStr
from app.crud_user import (
    crud_get_user_email,
    crud_record_password_test,
    crud_verify_token,
    new_reset_password,
    revoke_token,
    crud_get_verification,
    crud_verify_user,
    crud_create_user,
    crud_creat_verification,
    crud_updated_user,
    crud_read_users,
    crud_delete_user,
)
from fastapi.security import OAuth2PasswordRequestForm
from app.login_user import login_user
from app.security import oauth2_scheme
from app.tokens import verify_access_token,require_admin,verify_refresh_token,revoke_refresh_token
from app.database import get_db
from app.email_verification import create_hash_token,send_verification_email,send_password_reset_email
from models import User
import os
import uuid
import hashlib


router=APIRouter(
    prefix="/users",
    tags=["users"]
)
@router.get("/me",response_model=ResponseUser)
async def get_me(token:str = Depends(oauth2_scheme),db=Depends(get_db)):
    return verify_access_token(token,db)
@router.post("/forgot-password")
async def forgot_password(email:EmailStr,db:Session=Depends(get_db)):
    user=crud_get_user_email(email,db)
    token,token_hash,expires_at=create_hash_token()
    crud_record_password_test(user.id,token_hash,expires_at,db)
    send_password_reset_email(email,token)
    return {
        "message":"Please wait You will receive an email"
    }
@router.post("/reset-password")
async def reset_password(token:str,new_password:str,db:Session=Depends(get_db)):
    hash_token=hashlib.sha256(
        token.encode()
    ).hexdigest()
    user_id,token_hash=crud_verify_token(hash_token,db)
    new_reset_password(user_id,new_password,db)
    revoke_token(token_hash,db)
    return {
        "message":"Password changed successfullly"
    }
@router.get("/verify-email")
async def verify_email(token: str,db:Session=Depends(get_db)):
    token_hash=hashlib.sha256(
        token.encode()
    ).hexdigest()
    user_id=crud_get_verification(token_hash,db)
    crud_verify_user(user_id,db)
    return {
        "message":"Email verified successfully"
    }


@router.post('/')
async def create_users(user: CreateUser,db:Session=Depends(get_db)):
    user_id= crud_create_user(db,user)
    token,token_hash,expires_at=create_hash_token()
    crud_creat_verification(user_id,token_hash,expires_at,db)
    send_verification_email(user.email,token)
    return {
        "message":"User created successfully"
    }


@router.put("/user/{user_id}")
async def update_users(user_id:int,users:UpdatedUser,crruent_user=Depends(require_admin),db:Session=Depends(get_db)):
    return crud_updated_user(user_id,users,db)
@router.get("/user/{id}",response_model=ResponseUser)
async def get_user(id:int,db=Depends(get_db)):
    return crud_read_users(id,db)
@router.delete("/user/{user_id}")
async def deleted_user(user_id: int,current_user=Depends(require_admin),db:Session=Depends(get_db)):
    return crud_delete_user(user_id,db)
@router.post("/login",response_model=RespondeLogin)
async def Login_users(db:Session=Depends(get_db),data: OAuth2PasswordRequestForm=Depends()):
    return login_user(db,data)
@router.post("/refresh")
async def refresh_token(refresh_token:str,db:Session=Depends(get_db)):
    verify_refresh_token(refresh_token,db)
    return revoke_refresh_token(refresh_token,db)
@router.post("/user/{user_id}/avatars")
async def uploads_user_profile(user_id:int,file:UploadFile=File(...),current_user=Depends(require_admin),db:Session=Depends(get_db)):
    path=None
    db_updated=False
    try:
        if file.content_type not in ["image/png","image/jpeg"]:
            raise HTTPException(
                status_code=415,
                detail="Incorrect type"
            )
        content=await file.read()
        content_bytes=content[:8]
        JPEG_SIGNATURE=b"\xff\xd8\xff"
        PNG_SIGNATURE=b"\x89PNG\r\n\x1a\n"
        if file.content_type=="image/png" and not content_bytes.startswith(PNG_SIGNATURE):
            raise HTTPException(
                status_code=415,
                detail="Incorrect type"
            )
        if file.content_type=="image/jpeg" and not content_bytes.startswith(JPEG_SIGNATURE):
            raise HTTPException(
                status_code=415,
                detail="Incorrect type"
            )
        if len(content)>(1*1024)*1024:
            raise HTTPException(
                status_code=413,
                detail="This file exceeds the allowed size"
            )
        data = db.get(User,user_id)
        if data is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        if file.content_type=="image/png":
            extension=".png"
        elif file.content_type=="image/jpeg":
            extension=".jpg"
        path=os.path.join("avatars",f"{uuid.uuid4()}{extension}")
        with open(path, "wb") as f:
            f.write(content)
        data.image_profile=path
        db.commit()
        old_image=data.image_profile
        db_updated=True
        if old_image is not None:
            if os.path.exists(old_image):
                os.remove(old_image)
    except HTTPException:
        raise
    except Exception:
        if not db_updated:
            if os.path.exists(path):
                os.remove(path)
                db.rollback()
            raise HTTPException(
                status_code=500,
                detail="It happened a wrong to saved the file in database"
                )
    return {
        "message":"the file saved successfully"
    }
