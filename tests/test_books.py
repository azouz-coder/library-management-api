from fastapi.testclient import TestClient
import os
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import User
import app.database as database
from app.database import create_db_engine,create_session_factory,get_db
import pytest
from app.main import app
from app.tokens import create_access_token
import app.users as users
@pytest.fixture
def test_db_engine():
    database.DATABASE_PATH="test_library_test.db"
    if os.path.exists("test_library_test.db"):
        os.remove("test_library_test.db")
    database.init_db()
    engine =create_db_engine("test_library_test.db")
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
    try:
        db=SessionLocal()
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
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_create_book_admin(client,db):
        book={
            "isbn":"10000",
            "title":"Test Book",
            "author":"Test Author"
        }
        user={
            "name":"test",
            "email":"test@example.com",
            "password":"testpassword"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email==user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response0=client.post("/books/",json=book,headers=headers)
        assert response0.status_code==200
def test_create_book_not_admin(client,db):
        book={
            "isbn":"1000",
            "title":"Test Book",
            "author":"Test Author"
        }
        user={
            "name":"Test",
            "email":"test@example.com",
            "password":"123456789"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User.id).where(User.email == user["email"])
        user_id = db.execute(stmt).scalar_one()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        response0=client.post("/books/",json=book,headers=headers)
        assert response0.status_code==403
def test_create_with_the_same_isbn(client,db):
        book={
            "isbn":"10000",
            "title":"Test Book",
            "author":"Test Author"
        }
        user={
            "name":"test",
            "email":"test@example.com",
            "password":"testpassword"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email == user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response0=client.post("/books/",json=book,headers=headers)
        assert response0.status_code==200
        response1=client.post("/books/",json=book,headers=headers)
        assert response1.status_code==409
def test_read_book(client,db):
        book={
            "isbn":"10000",
            "title":"Test Book",
            "author":"Test Author"
        }
        user={
            "name":"test",
            "email":"test@example.com",
            "password":"testpassword"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email == user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response0=client.post("/books/",json=book,headers=headers)
        assert response0.status_code==200
        isbn=book["isbn"]
        response1=client.get(f"/books/{isbn}")
        assert response1.status_code==200
        data_response=response1.json()
        assert data_response["isbn"]==book["isbn"]
        assert data_response["title"]==book["title"]
        assert data_response["author"]==book["author"]
def test_read_book_not_found(client):
    response=client.get(f"/books/{1}")
    assert response.status_code==404
def test_search_with_isbn_author_title(client,db):
        book1={
            "isbn":"10000",
            "title":"Test Book",
            "author":"Test Author"
        }
        book2={
            "isbn":"10001",
            "title":"Clean Code",
            "author":"python API"
        }
        book3={
            "isbn":"10002",
            "title":"Clean Test",
            "author":"python test"
        }
        user={
            "name":"test",
            "email":"test@example.com",
            "password":"testpassword"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email == user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response1=client.post("/books/",json=book1,headers=headers)
        assert response1.status_code==200
        response2=client.post("/books/",json=book2,headers=headers)
        assert response2.status_code==200
        response3=client.post("/books/",json=book3,headers=headers)
        assert response3.status_code==200
        response4=client.get("/books/?search=python")
        assert response4.status_code==200
        data_response_4=response4.json()
        assert len(data_response_4["items"])==2
        assert data_response_4["items"][0]["isbn"]=="10001"
        assert data_response_4["items"][1]["isbn"]=="10002"
        response5=client.get("/books/?search=Test")
        data_response_5=response5.json()
        assert response5.status_code==200
        assert len(data_response_5["items"])==2
        assert data_response_5["items"][0]["isbn"]=="10002"
        assert data_response_5["items"][1]["isbn"]=="10000"
        response6=client.get("/books/?search=10000")
        assert response6.status_code==200
        data_response_6=response6.json()
        assert len(data_response_6["items"])==1
        assert data_response_6["items"][0]["isbn"]=="10000"
def test_updated_book_admin(client,db):
        book={
            "isbn":"1000",
            "title":"Test Book",
            "author":"Test Author"
        }
        user={
            "name":"Test",
            "email":"test@example.com",
            "password":"123456789"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email == user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response0=client.post("/books/",json=book,headers=headers)
        assert response0.status_code==200
        response1=client.put(f"/books/1000",json={"title":"Test Updatbook","author":"Testupdate"},headers=headers)
        assert response1.status_code==200
        response2=client.get("/books/1000")
        assert response2.status_code==200
        data_response=response2.json()
        assert data_response["title"]=="Test Updatbook"
        assert data_response["author"]=="Testupdate"
def test_updated_book_not_found(client,db):
        user={
            "name":"Test",
            "email":"test@example.com",
            "password":"123456789"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email == user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response=client.put("/books/1000",json={"title":"fialed","author":"fialed"},headers=headers)
        assert response.status_code==404
def test_updated_book_user(client,db):
        user={
            "name":"Test",
            "email":"test@example.com",
            "password":"123456789"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User.id).where(User.email == user["email"])
        user_id = db.execute(stmt).scalar_one()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        response1=client.put("/books/1000",json={"title":"test","author":"test"},headers=headers)
        assert response1.status_code==403
def test_delete_book_admin(client,db):
        book={
            "isbn":"10000",
            "title":"Test Book",
            "author":"Test Author"
        }
        user={
            "name":"test",
            "email":"test@example.com",
            "password":"testpassword"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email == user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response0=client.post("/books/",json=book,headers=headers)
        assert response0.status_code==200
        response1=client.delete("/books/10000",headers=headers)
        assert response1.status_code==200
        response2=client.get("/books/10000")
        assert response2.status_code==404
def test_delete_book_not_found(client,db):
        user={
            "name":"Test",
            "email":"test@example.com",
            "password":"123456789"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email == user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response=client.delete("/books/1000",headers=headers)
        assert response.status_code==404
def test_delet_book_user(client,db):
        user={
            "name":"Test",
            "email":"test@example.com",
            "password":"123456789"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User.id).where(User.email==user["email"])
        user_id = db.execute(stmt).scalar_one()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        response1=client.delete("/books/1000",headers=headers)
        assert response1.status_code==403
def test_pagination(client,db):
        book1={
            "isbn":"10000",
            "title":"Test Book",
            "author":"Test Author"
        }
        book2={
            "isbn":"10001",
            "title":"Clean Code",
            "author":"python API"
        }
        book3={
            "isbn":"10002",
            "title":"Clean Test",
            "author":"python test"
        }
        user={
            "name":"test",
            "email":"test@example.com",
            "password":"testpassword"
        }
        response=client.post("/users/",json=user)
        assert response.status_code==200
        stmt = select(User).where(User.email == user["email"])
        data = db.execute(stmt).scalar_one()
        data.role = "admin"
        db.commit()
        token=create_access_token(data={"sub":str(data.id)})
        headers={"Authorization":f"Bearer {token}"}
        response1=client.post("/books/",json=book1,headers=headers)
        assert response1.status_code==200
        response2=client.post("/books/",json=book2,headers=headers)
        assert response2.status_code==200
        response3=client.post("/books/",json=book3,headers=headers)
        assert response3.status_code==200
        response4=client.get("/books/?limit=1&offset=1")
        assert response4.status_code==200
        data_response=response4.json()
        assert data_response["items"][0]["isbn"]=="10002"