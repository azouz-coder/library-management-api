import pytest
import os
from fastapi.testclient import TestClient
import app.database as database
from app.database import create_db_engine,create_session_factory,get_db
from app.main import app 
from app.tokens import create_access_token
import app.users as users
from sqlalchemy import select
from app.models import User,Book,Borrowing
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
def test_borrowing_book(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==200
def test_borrowing_book_not_found(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}

        resoponse_3=client.post("/borrowing/",json={"isbn":"222222","user_id":user_id},headers=headers)
        assert resoponse_3.status_code==404
def test_borrowing_book_borrowed(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==200
        resoponse_4=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_4.status_code==409
def test_return_book_not_borrowed(client,db):
        user={
            "name":"azouz",
            "email":"testborrowing@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.put("/borrowing/",params={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==404

def test_return_book_borrowed(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==200
        resoponse_4=client.put("/borrowing/",params={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_4.status_code==200
        data=db.get(Borrowing,user_id)
        returned_at=data.returned_at
        assert returned_at is not None
def test_borrowing_book_user_not_found(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":22222},headers=headers)
        assert resoponse_3.status_code==404
def test_return_book_user_not_found(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==200
        resoponse_4=client.put("/borrowing/",params={"isbn":book["isbn"],"user_id":2222},headers=headers)
        assert resoponse_4.status_code==404
def test_delete_borrowing_not_returned(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==200
        row=db.get(Borrowing,user_id)
        resoponse_4=client.delete(f"/borrowing/{row.id}")
        assert resoponse_4.status_code==409
def test_delete_borrowing_retuned(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==200
        row=db.get(Borrowing,user_id)
        resoponse_4=client.put("/borrowing/",params={"isbn":book["isbn"],'user_id':user_id},headers=headers)
        assert resoponse_4.status_code==200
        resoponse_5=client.delete(f"/borrowing/{row.id}")
        assert resoponse_5.status_code==200
        db.expunge_all()
        delete_row=db.get(Borrowing,row.id)
        assert delete_row is None
def test_read_all_borrowing(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==200
        resoponse_4=client.get("/borrowing/borrow")
        assert resoponse_4.status_code==200
        data=resoponse_4.json()
        assert "azouz" == data[0]["name"]
def test_read_all_borrowing_not_found(client):
    resoponse=client.get("/borrowing/borrow")
    assert resoponse.status_code==404
def test_read_brrowed_found(client,db):
        user={
            "name":"azouz",
            "email":"testborrow@gamil.com",
            "password":"test12345"
        }
        book={
            "isbn":"1234",
            "title":"borrowin",
            "author":"azouz"
        }
        resoponse_1=client.post("/users/",json=user)
        assert resoponse_1.status_code==200
        stmt = select(User).where(User.email==user["email"])
        result = db.execute(stmt).scalar_one_or_none()
        user_id=result.id
        result.role="admin"
        db.commit()
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"Bearer {token}"}
        resoponse_2=client.post("/books/",json=book,headers=headers)
        assert resoponse_2.status_code==200
        resoponse_3=client.post("/borrowing/",json={"isbn":book["isbn"],"user_id":user_id},headers=headers)
        assert resoponse_3.status_code==200
        row=db.get(Borrowing,user_id)
        resoponse_4=client.get(f"/borrowing/{row.id}")
        assert resoponse_4.status_code==200
        data=resoponse_4.json()
        assert "azouz" == data["name"]
def test_read_borrowed_not_found(client):
    resoponse=client.get(f"/borrowing/{34}")
    assert resoponse.status_code==404


        