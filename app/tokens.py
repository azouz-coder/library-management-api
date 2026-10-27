from jose import jwt , JWTError
from fastapi import HTTPException
from datetime import datetime,timezone,timedelta
import hashlib
import secrets
import os
from app.database import get_connection,get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.security import oauth2_scheme
from fastapi import Depends
from dotenv import load_dotenv
from models import RefreshTokens
load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM="HS256"
EXPIRE_ACCESS_TOKEN=30
def create_access_token(data:dict):
    expire=datetime.now(timezone.utc)+timedelta(minutes=EXPIRE_ACCESS_TOKEN)
    to_encode=data.copy()
    to_encode["exp"]=expire
    to_encode["token_type"]="access"
    jwt_encode=jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return jwt_encode
def verify_access_token(token:str,db=Depends(get_db)):
    try:
        payload=jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id=payload.get("sub")
        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid Token"
            )
        if  user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid Token"
            )
        from app.crud_user import crud_read_users
        return crud_read_users(int(user_id),db)
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid"
        )

def require_admin(db=Depends(get_db),token:str=Depends(oauth2_scheme)):
    row=verify_access_token(token,db)
    if row["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission"
        )

def create_refresh_token(user_id:int,db:Session):
    try:
        refresh_token=secrets.token_urlsafe(32)
        hash_refresh_token=hashlib.sha256(
            refresh_token.encode()
        ).hexdigest()
        create_at=datetime.now(timezone.utc)
        expire_at=create_at+timedelta(days=7)
        create_at=create_at.isoformat()
        expire_at=expire_at.isoformat()
        revoked=False
        new_refresh_token = RefreshTokens(user_id=user_id,hash_token=hash_refresh_token,create_at=create_at,expire_at=expire_at,revoked=revoked)
        db.add(new_refresh_token)
        db.commit()
        return refresh_token,hash_refresh_token,create_at,expire_at,revoked
    except Exception:
        db.rollback()
        raise
def verify_refresh_token(refresh_token:str,db:Session):
    try:
        hash_refresh_token=hashlib.sha256(
            refresh_token.encode()
        ).hexdigest()
        stmt = select(RefreshTokens).where(RefreshTokens.hash_token==hash_refresh_token)
        data = db.execute(stmt).scalar_one_or_none()
        if data is None:
            raise HTTPException(
                status_code=401,
                detail="Invialid refresh token"
            )
        expire=datetime.fromisoformat(data.expire_at)
        if datetime.now(timezone.utc) > expire:
            raise HTTPException(
                status_code=401,
                detail="Refresh token expired"
            )
        if data.revoked:
            raise HTTPException(
                status_code=401,
                detail="Refresh token is revoked"
            )
        return data
    except HTTPException:
        raise
def revoke_refresh_token(refresh_token:str,db:Session):
    try:
        hash_refresh_token=hashlib.sha256(
            refresh_token.encode()
        ).hexdigest()
        stmt = select(RefreshTokens).where(RefreshTokens.hash_token==hash_refresh_token)
        data = db.execute(stmt).scalar_one_or_none()
        if data is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        data.revoked=True
        new_access_token=create_access_token(data={"sub":str(data.id)})
        new_refresh_token=create_refresh_token(data.id)
        return {
            "access_token":new_access_token,
            "refresh_token":new_refresh_token[0],
            "token_type":"bearer"
        }
    except HTTPException:
        raise

    

