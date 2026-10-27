from app.security import hash_password
from fastapi import HTTPException
from app.schema import EmailStr
from datetime import datetime,timezone
from sqlalchemy import select,and_
from sqlalchemy.orm import Session
from models import User,EmailVerification,PasswordResets
from app.loggin_config import logger

def crud_create_user(db:Session,user):
    try:
        stmt = select(User.email).where(User.email==user.email)
        email = db.execute(stmt).scalar_one_or_none()
        
        if email is not None:
            logger.warning("User already to creat , Email found")
            raise HTTPException(
            status_code=409,
            detail="User already to create"
            )
        new_user=User(name=user.name,email=user.email,password=hash_password(user.password),role="user")
        db.add(new_user)
        db.commit()
        logger.info("User created successfully")
        user_id=new_user.id
        return user_id
    
    except HTTPException:
        raise
    except Exception:
            db.rollback()
            logger.exception("Unexpected error")
            raise
def crud_read_users(user_id:int,db:Session):
        user = db.get(User,user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            ) 
        return {
            "name":user.name,
            "email":user.email,
            "role":user.role
         }

def crud_updated_user(user_id:int,users,db:Session):
    try:
        user = db.get(User,user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        if users.name is not None:
            user.name = users.name
        if users.email is not None:
            stmt = select(User).where(User.email==users.email,User.id!=user_id)
            data = db.execute(stmt).scalar_one_or_none()
            if data is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Invaled inforamtions"
                )
            user.email = users.email
        if users.name is None and users.email is None :
            raise HTTPException(
                status_code=400,
                detail="No fields provided"
            )
        db.commit()
        return {
            "message":"User updated successfully."
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

def crud_delete_user(user_id:int,db:Session):
    try:
        user = db.get(User,user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        db.delete(user)
        db.commit()
    
        return {
            "message":"User deleted successfully"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

def crud_get_user_email(email:EmailStr,db:Session):
        stmt = select(User).where(User.email == email)
        user = db.execute(stmt).scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        return user
def crud_creat_verification(user_id: int , token_hash: str , expires_at: datetime,db:Session):

    try:
        expires_at=datetime.isoformat(expires_at)
        new_verification = EmailVerification(user_id=user_id,token_hash=token_hash,expires_at=expires_at)
        db.add(new_verification)
        db.commit()
    except Exception:
        db.rollback()
        raise
def crud_get_verification(token_hash: str,db:Session):
 
    try:
    
        stmt = select(EmailVerification).where(EmailVerification.token_hash==token_hash)
        virification = db.execute(stmt).scalar_one_or_none()
        
        if virification is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid verification token"
            )
        expires_at=datetime.fromisoformat(virification.expires_at)
        now=datetime.now(timezone.utc)
        if expires_at < now:
            raise HTTPException(
                status_code=401,
                detail="Verification token expired"
            )
        used=virification.used
        if used:
            raise HTTPException(
                status_code=401,
                detail="The token is used"
            )
        virification.used = True
        db.commit()
        return virification.user_id
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
    
def crud_verify_user(user_id: int,db:Session):
    try:
        user = db.get(User,user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        user.is_verified = True
        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

def crud_record_password_test(user_id:int,token_hash:str,expires_at: datetime,db:Session):
  
    try:
        expires_at=datetime.isoformat(expires_at)
        new_record = PasswordResets(user_id = user_id,token_hash = token_hash,expires_at=expires_at,used=False)
        db.add(new_record)
        db.commit()
    except Exception:
        db.rollback()
        raise
def crud_verify_token(token_hash:str,db:Session):
        stmt = select(PasswordResets).where(PasswordResets.token_hash==token_hash)
        password_reset = db.execute(stmt).scalar_one_or_none()
        if password_reset is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid verified token"
            )
        expires_at=datetime.fromisoformat(password_reset.expires_at)
        now=datetime.now(timezone.utc)
        if now > expires_at:
            raise HTTPException(
                status_code=401,
                detail="Invalid verified token, Time out"
            )
        used=password_reset.used
        if used:
            raise HTTPException(
                status_code=401,
                detail="Invalid verified token "
            )
        return password_reset.user_id,password_reset.token_hash
def new_reset_password(user_id:int,new_password:str,db:Session):
    try:
        hash_new_password=hash_password(new_password)
        user = db.get(User,user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        user.password  = hash_new_password
        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
def revoke_token(token_hash:str,db:Session):
    try:
        stmt = select(PasswordResets).where(PasswordResets.token_hash == token_hash)
        used = db.execute(stmt).scalar_one_or_none()
        if used is None:
            raise HTTPException(
                status_code=409,
                detail="Invalid token"
            )
        used.used = True
        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
