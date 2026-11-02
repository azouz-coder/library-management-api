import os
import pytest
from fastapi.testclient import TestClient
from app.database import create_db_engine, create_session_factory, get_db
from app.models import Base
from sqlalchemy.orm import Session
import app.users as users
from app.models import User
from app.main import app
from app.tokens import create_access_token
from unittest.mock import MagicMock
@pytest.fixture
def test_db_engine():
    if os.path.exists("test_library_test.db"):
        os.remove("test_library_test.db")
    engine= create_db_engine("test_library_test.db")
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
    monkeypatch.setattr(
        users,
        "send_verification_email",
        lambda email, token: None
    )
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
def create_test_user(db:Session):

        user = {
            "name": "test",
            "email": "upload@gmail.com",
            "password": "testupload"
        }

        # إنشاء المستخدم
        user_obj = User(name=user["name"], email=user["email"], password=user["password"], role="user", is_verified=True)
        db.add(user_obj)
        db.commit()

        # الحصول على user_id
        user_id = user_obj.id
        # تحويل المستخدم إلى admin
        user_obj.role = "admin"
        db.commit()

        # إنشاء Token
        token = create_access_token(
            data={"sub": str(user_id)}
        )

        headers = {
            "Authorization": f"bearer {token}"
        }

        return user_id, headers



def test_upload_jpg(client,db:Session):
    user_id, headers = create_test_user(db)

    with open("test_image.jpg", "rb") as f:
        content = f.read()

    response = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "test.jpg",
                content,
                "image/jpeg"
            )
        },
        headers=headers
    )

    assert response.status_code == 200
    user = db.get(User,user_id)
    assert user.image_profile is not None


def test_upload_png(client,db:Session):
    user_id, headers = create_test_user(db)

    with open("test_image.png", "rb") as f:
        content = f.read()

    response = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "test.png",
                content,
                "image/png"
            )
        },
        headers=headers
    )

    assert response.status_code == 200
    user = db.get(User,user_id)
    assert user.image_profile is not None
def test_upload_invalid_type(client,db:Session):
    user_id, headers = create_test_user(db)

    with open("test_image.ico", "rb") as f:
        content = f.read()

    response = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "test.ico",
                content,
                "image/x-icon"
            )
        },
        headers=headers
    )

    assert response.status_code == 415


def test_upload_fake_jpeg(client,db:Session):
    user_id, headers = create_test_user(db)

    with open("test_image.jpg", "rb") as f:
        content = b"fakejpeg" + f.read()

    response = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "test.jpg",
                content,
                "image/jpeg"
            )
        },
        headers=headers
    )

    assert response.status_code == 415


def test_upload_too_large_file(client,db:Session):
    user_id, headers = create_test_user(db)

    content = (
        b"\x89PNG\r\n\x1a\n"
        + os.urandom((2 * 1024) * 1024 + 1)
    )

    response = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "test_image_large.png",
                content,
                "image/png"
            )
        },
        headers=headers
    )

    assert response.status_code == 413


def test_upload_user_not_found(client,db:Session):
    _, headers = create_test_user(db)

    with open("test_image.jpg", "rb") as f:
        content = f.read()

    user_id = 9999

    response = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "test.jpg",
                content,
                "image/jpeg"
            )
        },
        headers=headers
    )

    assert response.status_code == 404


def test_upload_file_exists(client,db:Session):
    user_id, headers = create_test_user(db)

    with open("test_image.jpg", "rb") as f:
        content = f.read()

    response = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "test.jpg",
                content,
                "image/jpeg"
            )
        },
        headers=headers
    )

    assert response.status_code == 200
    user = db.get(User,user_id)
    db.expire(user)
    assert os.path.exists(user.image_profile)


def test_upload_file_remove_old_file(client,db:Session):
    user_id, headers = create_test_user(db)

    with open("carbon (49).png", "rb") as f:
        content = f.read()

    response1 = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "carbon (49).png",
                content,
                "image/png"
            )
        },
        headers=headers
    )

    assert response1.status_code == 200
    user = db.get(User,user_id)
    db.expire(user)
    old_image_path = user.image_profile

    with open("watsup.jpeg", "rb") as f:
        content = f.read()

    response2 = client.post(
        f"/users/user/{user_id}/avatars",
        files={
            "file": (
                "watsup.jpeg",
                content,
                "image/jpeg"
            )
        },
        headers=headers
    )

    assert response2.status_code == 200
    user = db.get(User,user_id)
    db.expire(user)
    new_image_path = user.image_profile

    assert new_image_path != old_image_path
    assert not os.path.exists(old_image_path)
    assert os.path.exists(new_image_path)



def test_upload_db_failure(client, db, monkeypatch):
    user_id, headers = create_test_user(db)

    # 1) session مزيّف: كل شيء حقيقي، إلا commit يفشل
    broken_db = MagicMock(wraps=db)
    broken_db.commit.side_effect = Exception("Database error")
    app.dependency_overrides[get_db] = lambda: broken_db

    # 2) نسجّل الملفات قبل الطلب
    files_before = set(os.listdir("avatars"))

    # 3) نرسل الصورة
    with open("test_image.jpg", "rb") as f:
        content = f.read()

    response = client.post(
        f"/users/user/{user_id}/avatars",
        files={"file": ("test.jpg", content, "image/jpeg")},
        headers=headers,
    )

    # 4) نتحقق
    assert response.status_code == 500
    assert set(os.listdir("avatars")) == files_before

    app.dependency_overrides.clear()
