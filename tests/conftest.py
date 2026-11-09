import os

# Give the test suite a JWT secret so it can run without a real .env file.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
