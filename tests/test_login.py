import pytest
from fastapi.testclient import TestClient
import os 
from app.database import create_db_engine,create_session_factory, get_db
import hashlib
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime,timezone,timedelta
from app.main import app
import app.users as users
from app.models import Base,User,RefreshTokens
@pytest.fixture
def test_db_engine():
    if os.path.exists("test_library_test.db"):
        os.remove("test_library_test.db")
    engine =   create_db_engine("test_library_test.db")
    Base.metadata.create_all(bind=engine)
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
    SessionLocal = create_session_factory(test_db_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(monkeypatch,test_db_engine):
        monkeypatch.setattr(users,"send_verification_email",lambda email,token:None)
        SessionLocal = create_session_factory(test_db_engine)
        def override_get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
        app.dependency_overrides[get_db] = override_get_db
        db = SessionLocal()
        test_client=TestClient(app)
        try:
            user={
                "name":"azouz",
                "email":"azouz@gmail.com",
                "password":"testazouz"
            }
            response=test_client.post("/users/",json=user)
            assert response.status_code==200
            stmt = select(User).where(User.email == user["email"])
            user = db.execute(stmt).scalars().first()
            user.is_verified = True
            db.commit()
            yield test_client
        finally:
            test_client.close()
            db.close()
            app.dependency_overrides.clear()
def test_login_success(client):
        response=client.post("/users/login",data={"username":"azouz@gmail.com","password":"testazouz"})
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
def test_refresh_token(client):
        response=client.post("/users/login",data={"username":"azouz@gmail.com","password":"testazouz"})
        refresh_token=response.json()["refresh_token"]
        response_refresh_token=client.post("/users/refresh",params={"refresh_token":refresh_token})
        assert response_refresh_token.status_code == 200
        assert "access_token" in response_refresh_token.json()
        assert "refresh_token" in response_refresh_token.json()
        assert "token_type" in response_refresh_token.json()
        response_refresh_token=client.post("/users/refresh",params={"refresh_token":refresh_token})
        assert response_refresh_token.status_code == 401
def test_refresh_expired_token(client,db:Session):
        response=client.post("/users/login",data={"username":"azouz@gmail.com","password":"testazouz"})
        refresh_token=response.json()["refresh_token"]
        hash_refresh_token=hashlib.sha256(
        refresh_token.encode()
        ).hexdigest()
        time=datetime.isoformat(datetime.now(timezone.utc)-timedelta(hours=1))
        stmt = select(RefreshTokens).where(RefreshTokens.hash_token == hash_refresh_token)
        token = db.execute(stmt).scalars().first()
        token.expire_at=time
        db.commit()
        response_refresh_token=client.post("/users/refresh",params={"refresh_token":refresh_token})
        assert response_refresh_token.status_code == 401
def test_revoke_token(client,db:Session):
        response=client.post("/users/login",data={"username":"azouz@gmail.com","password":"testazouz"})
        refresh_token=response.json()["refresh_token"]
        hash_refresh_token=hashlib.sha256(
        refresh_token.encode()
        ).hexdigest()
        stmt = select(RefreshTokens).where(RefreshTokens.hash_token == hash_refresh_token)
        token = db.execute(stmt).scalars().first()
        token.revoked = True
        db.commit()
        response_refresh_token=client.post("/users/refresh",params={"refresh_token":refresh_token})
        assert response_refresh_token.status_code == 401
       
def test_refresh_invalid_token(client):
        response=client.post("/users/refresh",params={"refresh_token":"asdkfjasierpaweorjsdjfkawpeoiruisdf"})
        assert response.status_code == 401

def test_login_wrong_password(client):
        response=client.post("/users/login",data={"username":"azouz@gmail.com","password":"testtest"})
        assert response.status_code == 401
def test_login_unknown_email(client):
        response=client.post("/users/login",data={"username":"test@gmail.com","password":"testazouz"})
        assert response.status_code == 401