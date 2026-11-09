import pytest
import os
import app.database as database
from app.main import app
from fastapi.testclient import TestClient
from app.tokens import create_access_token
import app.book as book
import app.users as users
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Base
@pytest.fixture
def test_db_engine():
    if os.path.exists("test_library_test.db"):
        os.remove("test_library_test.db")
    engine= database.create_db_engine("test_library_test.db")
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
    SessionLocal = database.create_session_factory(test_db_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@pytest.fixture
def client(monkeypatch,test_db_engine):
    monkeypatch.setattr(users,"send_verification_email",lambda email,token:None)
    SessionLocal = database.create_session_factory(test_db_engine)
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[database.get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
def test_upload_file(client,db:Session):
        book={
            "isbn":"10012",
            "title":"testupload",
            "author":"testone"
        }
        user={
            "name":"testing",
            "email":"upload@gamil.com",
            "password":"test1234"
        }
        isbn=book["isbn"]
        response_1=client.post("/users/",json=user)
        assert response_1.status_code==200
        stmt = select(users.User).where(users.User.email == user["email"])
        result = db.execute(stmt).scalars().first()
        result.role = "admin"
        db.commit()
        user_id = result.id
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"bearer {token}"}
        response_2=client.post("/books/",json=book,headers=headers)
        assert response_2.status_code==200
        with open("test_image.png","rb") as f:
            content=f.read()

        response_3=client.post(f"/books/{isbn}/uploads",files={
            "file":(
                "test.png",
                content,
                "image/png"
            )
        },headers=headers)

        assert response_3.status_code==200
def test_image_not_true(client,db:Session):
        book={
            "isbn":"10012",
            "title":"testupload",
            "author":"testone"
        }
        user={
            "name":"testing",
            "email":"upload@gamil.com",
            "password":"test1234"
        }
        isbn=book["isbn"]
        response_1=client.post("/users/",json=user)
        assert response_1.status_code==200
        stmt = select(users.User).where(users.User.email == user["email"])
        result = db.execute(stmt).scalars().first()
        result.role = "admin"
        db.commit()
        user_id = result.id
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"bearer {token}"}
        response_2=client.post("/books/",json=book,headers=headers)
        assert response_2.status_code==200
        with open("test_image.png","rb") as f:
            content=b"this is not real image png" + f.read()
        response_3=client.post(f"/books/{isbn}/uploads",files={
            "file":(
                "test.png",
                content,
                "image/png"
            )
        },headers=headers)
        assert response_3.status_code==415
def test_file_too_big(client,db:Session):
        book_1={
            "isbn":"10012",
            "title":"testupload",
            "author":"testone"
        }
        user={
            "name":"testing",
            "email":"upload@gamil.com",
            "password":"test1234"
        }
        isbn=book_1["isbn"]
        response_1=client.post("/users/",json=user)
        assert response_1.status_code==200
        stmt = select(users.User).where(users.User.email == user["email"])
        result = db.execute(stmt).scalars().first()
        result.role = "admin"
        db.commit()
        user_id = result.id
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"bearer {token}"}
        response_2=client.post("/books/",json=book_1,headers=headers)
        assert response_2.status_code==200
        with open("large_file.png","wb") as f:
            f.write(b"a"*(8*1024)*1024)
        with open("large_file.png","rb") as f:
            content=b"\x89PNG\r\n\x1a\n"+f.read()
        response_3=client.post(f"/books/{isbn}/uploads",files={
            "file":(
                "large_file.png",
                content,
                "image/png"
            )
        },headers=headers)
        assert response_3.status_code==413
def test_isbn_not_found(client,db:Session):
    user={
        "name":"testing",
        "email":"upload@gamil.com",
        "password":"test1234"
    }
    response_1=client.post("/users/",json=user)
    assert response_1.status_code==200
    stmt = select(users.User).where(users.User.email == user["email"])
    result = db.execute(stmt).scalars().first()
    result.role = "admin"
    db.commit()
    user_id = result.id
    token=create_access_token(data={"sub":str(user_id)})
    headers={"Authorization":f"bearer {token}"}
    with open("test_image.png","rb") as f:
        content=f.read()
    response=client.post(f"/books/{9999999}/uploads",files={
        "file":(
            "test.png",
            content,
            "image/png"
        )
    },headers=headers)
    assert response.status_code==404
def test_upload_fialed_database(client,db:Session,monkeypatch):

        book_1={
            "isbn":"10012",
            "title":"testupload",
            "author":"testone"
        }
        user={
            "name":"testing",
            "email":"upload@gamil.com",
            "password":"test1234"
        }
        isbn=book_1["isbn"]
        response_1=client.post("/users/",json=user)
        assert response_1.status_code==200
        stmt = select(users.User).where(users.User.email == user["email"])
        result = db.execute(stmt).scalars().first()
        result.role = "admin"
        db.commit()
        user_id = result.id
        token=create_access_token(data={"sub":str(user_id)})
        headers={"Authorization":f"bearer {token}"}
        response_2=client.post("/books/",json=book_1,headers=headers)
        assert response_2.status_code==200
        files_before=set(os.listdir("uploads"))
        with open("test_image.png","rb") as f:
            content=f.read()
        def fail_commit(self):
            raise Exception("Database commit failed")
        monkeypatch.setattr(Session,"commit",fail_commit)
        response_3=client.post(f"/books/{isbn}/uploads",files={
            "file":(
                "test.png",
                content,
                "image/png"
            )
        },headers=headers)

        assert response_3.status_code==500
        files_after=set(os.listdir("uploads"))
        assert files_after==files_before
def test_upload_book_image_requires_login(client):
    response=client.post("/books/10012/uploads",files={
        "file":(
            "test.png",
            b"\x89PNG\r\n\x1a\n",
            "image/png"
        )
    })
    assert response.status_code==401
def test_upload_book_image_requires_admin(client,db:Session):
    user={
        "name":"testing",
        "email":"upload@gamil.com",
        "password":"test1234"
    }
    response_1=client.post("/users/",json=user)
    assert response_1.status_code==200
    stmt = select(users.User).where(users.User.email == user["email"])
    result = db.execute(stmt).scalars().first()
    user_id = result.id
    token=create_access_token(data={"sub":str(user_id)})
    headers={"Authorization":f"bearer {token}"}
    response=client.post("/books/10012/uploads",files={
        "file":(
            "test.png",
            b"\x89PNG\r\n\x1a\n",
            "image/png"
        )
    },headers=headers)
    assert response.status_code==403
