from fastapi.security import OAuth2PasswordRequestForm 
from fastapi import Depends,HTTPException
from typing import Annotated
from app.crud_user import crud_get_user_email
from app.security import verify_password
from app.tokens import create_access_token,create_refresh_token
from app.loggin_config import logger
from sqlalchemy.orm import Session
from app.database import get_db
def login_user(db:Annotated[Session,Depends(get_db)],data: Annotated[OAuth2PasswordRequestForm,Depends()]):
    try:
        row=crud_get_user_email(data.username,db)
        verified=verify_password(
            data.password,
            row.password
        )
        if not verified:
            logger.warning("Failed login attempt")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        is_verified=row.is_verified
        if not is_verified:
            logger.warning("Email not verified")
            raise HTTPException(
                status_code=403,
                detail="Please verify your email"
            )
        access_token=create_access_token(data={"sub":str(row.id)})
        refresh_token=create_refresh_token(row.id,db)
        logger.info("User login successfully.")
        return {
            "access_token":access_token,
            "refresh_token":refresh_token[0],
            "token_type":"bearer"
            }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error")
        raise