from fastapi.testclient import TestClient
import pytest
from app.main import app
import os 
import app.database as database
from app.database import create_db_engine,create_session_factory,get_db
import app.users as users
import hashlib
from datetime import datetime,timezone,timedelta
from app.tokens import create_access_token,SECRET_KEY,ALGORITHM
from jose import jwt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import User,EmailVerification,PasswordResets
saved_token=[]
def fake_send_verification_email(email,token):
    saved_token.append(token)
reset_token=[]
def fake_send_reset_password(email,token):
    reset_token.append(email)
    reset_token.append(token)
 
@pytest.fixture
def test_db_engine():
    database.DATABASE_PATH="test_library_test.db"
    if os.path.exists("test_library_test.db"):
        os.remove("test_library_test.db")
    database.init_db()
    engine = create_db_engine("test_library_test.db")
    try:
        yield engine
    finally:
        engine.dispose()
        try:
            if os.path.exists("test_library_test.db"):
                os.remove("test_library_test.db")
        except PermissionError:
            pass  
@pytest.fixture
def db(test_db_engine):
    SessionLocal = sessionmaker(test_db_engine)
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
@pytest.fixture
def client(test_db_engine,monkeypatch):
    monkeypatch.setattr(users,"send_verification_email",fake_send_verification_email)
    monkeypatch.setattr(users,"send_password_reset_email",fake_send_reset_password)
    SessionLocal = create_session_factory(test_db_engine)
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_verify_email(client,db):
        saved_token.clear()
        user={
            "name":"test",
            "email":"test@gmail.com",
            "password":"testtest"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code == 200
        response= client.get("/users/verify-email",params={"token":saved_token[-1]})
        assert response.status_code == 200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        assert result.is_verified == True
def test_verify_email_invalid_token(client):
    response=client.get("/users/verify-email",params={"token":"s;lakjdf;ajsd;klfja;ljdsfjadjfla"})
    assert response.status_code == 401
def test_verify_email_expired_token(client,db):
        user={
            "name":"test",
            "email":"test@gmail.com",
            "password":"testtest"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code == 200
        hash_token=hashlib.sha256(saved_token[-1].encode()).hexdigest()
        db.expire_all()
        time=datetime.isoformat(datetime.now(timezone.utc)-timedelta(hours=1))
        stmt = select(EmailVerification).where(EmailVerification.token_hash==hash_token)
        result = db.execute(stmt).scalar_one_or_none()
        assert result is not None
        result.expires_at=time
        db.commit()
        response=client.get("/users/verify-email",params={"token":saved_token[-1]})
        assert response.status_code == 401
def test_creat_user_duplicate_email(client):
    user={
        "name":"test",
        "email":"testr@gmail.com",
        "password":"testtest"
    }
    response1=client.post("/users/",json=user)
    assert response1.status_code == 200
    response2=client.post("/users/",json=user)
    assert response2.status_code == 409
def test_creat_user_invalid_email(client):
    user={
        "name":"test",
        "email":"not-an-email",
        "password":"testtest"
    }
    response=client.post("/users/",json=user)
    assert response.status_code == 422
def test_creat_user_without_row(client):
    user={
        "name":"test",
        "password":"testtest"
    }
    response=client.post("/users/",json=user)
    assert response.status_code == 422
def test_invalid_password(client):
    user={
        "name":"test",
        "email":"test@gmail.com",
        "password":"test"
    }
    response=client.post("/users/",json=user)
    assert response.status_code == 422
def test_forgot_password(client):
    user={
        "name":"test",
        "email":"test@gmail.com",
        "password":"12345678"
    }
    response0=client.post("/users/",json=user)
    assert response0.status_code==200
    response=client.post("/users/forgot-password",params={"email":user["email"]})
    assert response.status_code==200
    assert user["email"] in reset_token
    assert reset_token[1]
@pytest.fixture
def reset_data(client,db):
        reset_token.clear()
        user={
            "name":"test",
            "email":"test@gmail.com",
            "password":"12345678"
        }
        response0=client.post("/users/",json=user)
        assert response0.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        result.is_verified=True
        db.commit()
        response1=client.post('/users/forgot-password',params={"email":user["email"]})
        assert response1.status_code==200
        return user,reset_token[-1]
def test_reset_password_success(client,reset_data):
    user,token=reset_data
    response2=client.post("/users/reset-password",params={"token":token,"new_password":"azouzazouz"})
    assert response2.status_code==200
    response3=client.post("/users/login",data={"username":user["email"],"password":"12345678"})
    assert response3.status_code==401
    response4=client.post("/users/login",data={"username":user["email"],"password":"azouzazouz"})
    assert response4.status_code==200
def test_reset_invalid_token(client):
    response1=client.post("/users/reset-password",params={"token":"lskdjhglskdflgjslgjsk","new_password":"azouzazouz"})
    assert response1.status_code==401
def test_reset_expired_token(client,reset_data,db):
        user,token=reset_data
        hash_token=hashlib.sha256(token.encode()).hexdigest()
        time=datetime.isoformat(datetime.now(timezone.utc)-timedelta(hours=1))
        stmt = select(PasswordResets).where(PasswordResets.token_hash==hash_token)
        result  = db.execute(stmt).scalar_one_or_none()
        result.expires_at=time
        db.commit()
        response0=client.post("/users/reset-password",params={"token":token,"new_password":"azouzazouz"})
        assert response0.status_code==401
def test_reset_password_reuesd_token(client,reset_data):
    user,token=reset_data
    response=client.post("/users/reset-password",params={"token":token,"new_password":"azouzazouz"})
    assert response.status_code==200
    response0=client.post("/users/reset-password",params={"token":token, "new_password":"abdoabdo"})
    assert response0.status_code==401
def test_forgot_password_user_not_found(client):
    response=client.post("/users/forgot-password",params={"email":"azouz@gmail.com"})
    assert response.status_code==401
def test_read_user_id(client,db):
        user={
            "name":"tset",
            "email":"test@gmail.com",
            "password":"12345678"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        response2=client.get(f"/users/user/{user_id}")
        assert response2.status_code==200
def test_read_user_id_not_found(client):
    response=client.get(f"/users/user/{9999999}")
    assert response.status_code==404
def test_update_user(client,db):
        user={
            "name":"test",
            "email":"test@gmail.com",
            "password":"12345678"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        response2=client.put(f"/users/user/{user_id}",json={"name":"updated_name"},headers=headers)
        assert response2.status_code==403
def test_update_user_admin(client,db):
        user={
            "name":"test",
            "email":"test@gmail.com",
            "password":"123456789"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        response2=client.put(f"/users/user/{user_id}",json={"name":"updated_name"},headers=headers)
        assert response2.status_code==200
def test_delete_user(client,db):
        user={
            "name":"test",
            "email":"test@gmail.com",
            "password":"12345678"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        response2=client.delete(f"/users/user/{user_id}",headers=headers)
        assert response2.status_code==403
def test_delete_user_admin(client,db):
        user={
            "name":"test",
            "email":"test@gmail.com",
            "password":"123456789"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        response2=client.delete(f"/users/user/{user_id}",headers=headers)
        assert response2.status_code==200
def test_delete_user_not_found(client):
    token=create_access_token(data={"sub":str(9999999)})
    headers={"Authorization":f"Bearer {token}"}
    response=client.delete(f"/users/user/{9999999}",headers=headers)
    assert response.status_code==404
def test_get_me(client,db):
        user={
            "name":"test",
            "email":"test@gmail.com",
            "password":"123456789"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        response2=client.get("/users/me",headers=headers)
        assert response2.status_code==200
def test_get_me_invalid_token(client):
    headers={"Authorization":"Bearer invalid_token"}
    response=client.get("/users/me",headers=headers)
    assert response.status_code==401
def test_get_me_expired_token(client,db):
        user={
            "name":"test",
            "email":"test@gamil.com",
            "password":"123456789"
        }
        response1=client.post("/users/",json=user)
        assert response1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        expire_time=datetime.now(timezone.utc)-timedelta(hours=1)
        to_encode={"sub":str(user_id),"exp":expire_time,"token_type":"access"}
        token=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
        headers={"Authorization":f"Bearer {token}"}
        response2=client.get("/users/me",headers=headers)
        assert response2.status_code==401


